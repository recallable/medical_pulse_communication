"""
基于物品的协同过滤推荐算法
混合模式：用户行为相似度 + 课程属性相似度
"""
import logging
from collections import defaultdict

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from core.mongodb_client import mongodb_client_manager
from models import MedicalCourse
from models.schemas.behavior import ActionType

logger = logging.getLogger("api")

# MongoDB集合名称
USER_BEHAVIOR_COLLECTION = "user_behavior_log"


class ItemBasedCFRecommender:
    """基于物品的协同过滤推荐器"""
    
    # 行为权重配置
    BEHAVIOR_WEIGHTS = {
        ActionType.VIEW.value: 1.0,
        ActionType.FAVORITE.value: 3.0,
        ActionType.UNFAVORITE.value: -2.0,
        ActionType.PURCHASE.value: 5.0,
        ActionType.STUDY.value: 4.0,
        ActionType.RATE.value: 4.0,
    }
    
    # 属性相似度权重
    ATTRIBUTE_WEIGHT = 0.3  # 属性相似度占比
    BEHAVIOR_WEIGHT = 0.7   # 行为相似度占比
    
    def __init__(self):
        self._collection = None
    
    @property
    def collection(self):
        """获取MongoDB集合"""
        if self._collection is None:
            self._collection = mongodb_client_manager.get_collection(USER_BEHAVIOR_COLLECTION)
        return self._collection
    
    async def get_recommendations(
        self,
        user_id: int,
        top_n: int = 10,
        exclude_interacted: bool = True
    ) -> list[dict]:
        """
        获取推荐课程列表
        :param user_id: 用户ID
        :param top_n: 推荐数量
        :param exclude_interacted: 是否排除用户已交互的课程
        :return: 推荐课程列表
        """
        try:
            # 1. 获取用户交互过的课程
            user_courses = await self._get_user_interacted_courses(user_id)
            
            # 如果用户没有任何交互记录，返回热门课程（冷启动）
            if not user_courses:
                logger.info(f"用户 {user_id} 无交互记录，返回热门课程")
                return await self._get_hot_courses(top_n)
            
            # 2. 构建用户-物品评分矩阵
            user_item_matrix, course_ids, user_ids = await self._build_user_item_matrix()
            
            if len(course_ids) < 2:
                return await self._get_hot_courses(top_n)
            
            # 3. 计算物品相似度矩阵（混合模式）
            item_similarity = await self._compute_hybrid_similarity(user_item_matrix, course_ids)
            
            # 4. 为用户生成推荐
            recommendations = await self._generate_recommendations(
                user_id=user_id,
                user_courses=user_courses,
                item_similarity=item_similarity,
                course_ids=course_ids,
                user_item_matrix=user_item_matrix,
                user_ids=user_ids,
                top_n=top_n,
                exclude_interacted=exclude_interacted
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            # 发生错误时返回热门课程
            return await self._get_hot_courses(top_n)
    
    async def _get_user_interacted_courses(self, user_id: int) -> dict[int, float]:
        """
        获取用户交互过的课程及其评分
        :return: {course_id: weighted_score}
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$course_id",
                "total_weight": {"$sum": "$action_value"},
                "actions": {"$push": "$action_type"}
            }}
        ]
        
        result = {}
        async for doc in self.collection.aggregate(pipeline):
            result[doc["_id"]] = doc["total_weight"]
        
        return result
    
    async def _build_user_item_matrix(self) -> tuple[np.ndarray, list[int], list[int]]:
        """
        构建用户-物品评分矩阵
        :return: (矩阵, 课程ID列表, 用户ID列表)
        """
        # 聚合所有用户对课程的评分
        pipeline = [
            {"$group": {
                "_id": {"user_id": "$user_id", "course_id": "$course_id"},
                "total_weight": {"$sum": "$action_value"}
            }}
        ]
        
        # 收集数据
        user_course_scores = defaultdict(dict)
        all_courses = set()
        all_users = set()
        
        async for doc in self.collection.aggregate(pipeline):
            user_id = doc["_id"]["user_id"]
            course_id = doc["_id"]["course_id"]
            score = doc["total_weight"]
            
            user_course_scores[user_id][course_id] = score
            all_courses.add(course_id)
            all_users.add(user_id)
        
        # 转换为矩阵
        course_ids = sorted(list(all_courses))
        user_ids = sorted(list(all_users))
        
        course_idx = {cid: idx for idx, cid in enumerate(course_ids)}
        user_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        
        matrix = np.zeros((len(user_ids), len(course_ids)))
        
        for user_id, courses in user_course_scores.items():
            for course_id, score in courses.items():
                matrix[user_idx[user_id]][course_idx[course_id]] = score
        
        return matrix, course_ids, user_ids
    
    async def _compute_hybrid_similarity(
        self,
        user_item_matrix: np.ndarray,
        course_ids: list[int]
    ) -> np.ndarray:
        """
        计算混合相似度矩阵（行为 + 属性）
        """
        # 1. 计算基于行为的物品相似度（余弦相似度）
        item_matrix = user_item_matrix.T  # 转置为物品-用户矩阵
        behavior_similarity = cosine_similarity(item_matrix)
        
        # 2. 计算基于属性的物品相似度
        attribute_similarity = await self._compute_attribute_similarity(course_ids)
        
        # 3. 混合两种相似度
        hybrid_similarity = (
            self.BEHAVIOR_WEIGHT * behavior_similarity +
            self.ATTRIBUTE_WEIGHT * attribute_similarity
        )
        
        return hybrid_similarity
    
    async def _compute_attribute_similarity(self, course_ids: list[int]) -> np.ndarray:
        """
        基于课程属性计算相似度
        属性：medical_department（科室）, difficulty_level（难度）, applicable_title（适用职称）
        """
        n = len(course_ids)
        similarity_matrix = np.zeros((n, n))
        
        # 获取课程属性
        courses = await MedicalCourse.filter(id__in=course_ids).all()
        course_attrs = {c.id: c for c in courses}
        
        for i, cid_i in enumerate(course_ids):
            for j, cid_j in enumerate(course_ids):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                elif i < j:
                    sim = self._calculate_attribute_similarity(
                        course_attrs.get(cid_i),
                        course_attrs.get(cid_j)
                    )
                    similarity_matrix[i][j] = sim
                    similarity_matrix[j][i] = sim
        
        return similarity_matrix
    
    def _calculate_attribute_similarity(self, course1, course2) -> float:
        """计算两个课程之间的属性相似度"""
        if not course1 or not course2:
            return 0.0
        
        score = 0.0
        
        # 科室相同 +0.5
        if course1.medical_department == course2.medical_department:
            score += 0.5
        
        # 难度等级差异（差异越小越相似）
        difficulty_diff = abs(course1.difficulty_level - course2.difficulty_level)
        score += max(0, 0.3 - difficulty_diff * 0.1)
        
        # 适用职称相同 +0.2
        if course1.applicable_title and course2.applicable_title:
            if course1.applicable_title == course2.applicable_title:
                score += 0.2
        
        return min(score, 1.0)
    
    async def _generate_recommendations(
        self,
        user_id: int,
        user_courses: dict[int, float],
        item_similarity: np.ndarray,
        course_ids: list[int],
        user_item_matrix: np.ndarray,
        user_ids: list[int],
        top_n: int,
        exclude_interacted: bool
    ) -> list[dict]:
        """生成推荐列表"""
        course_idx = {cid: idx for idx, cid in enumerate(course_ids)}
        
        # 计算每个候选课程的推荐分数
        candidate_scores = {}
        
        for candidate_id in course_ids:
            if exclude_interacted and candidate_id in user_courses:
                continue
            
            candidate_idx = course_idx[candidate_id]
            score = 0.0
            
            # 基于用户交互过的课程计算加权相似度
            for interacted_id, user_score in user_courses.items():
                if interacted_id in course_idx:
                    interacted_idx = course_idx[interacted_id]
                    similarity = item_similarity[candidate_idx][interacted_idx]
                    score += similarity * user_score
            
            if score > 0:
                candidate_scores[candidate_id] = score
        
        # 按分数排序
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # 获取课程详情
        recommendations = []
        for course_id, score in sorted_candidates:
            course = await MedicalCourse.get_or_none(id=course_id)
            if course and course.status == 1 and course.sale_status == 1:
                recommendations.append({
                    "course_id": course.id,
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "medical_department": course.medical_department,
                    "difficulty_level": course.difficulty_level,
                    "price": float(course.price),
                    "recommendation_score": round(score, 4),
                    "recommendation_reason": "基于您的学习历史推荐"
                })
        
        # 如果推荐不足，用热门课程补充
        if len(recommendations) < top_n:
            hot_courses = await self._get_hot_courses(
                top_n - len(recommendations),
                exclude_ids=[r["course_id"] for r in recommendations] + list(user_courses.keys())
            )
            for hc in hot_courses:
                hc["recommendation_reason"] = "热门课程推荐"
            recommendations.extend(hot_courses)
        
        return recommendations
    
    async def _get_hot_courses(self, top_n: int, exclude_ids: list[int] = None) -> list[dict]:
        """
        获取热门课程（冷启动兜底）
        基于行为日志统计热度
        """
        exclude_ids = exclude_ids or []
        
        # 从MongoDB统计课程热度
        pipeline = [
            {"$group": {
                "_id": "$course_id",
                "interaction_count": {"$sum": 1},
                "total_weight": {"$sum": "$action_value"}
            }},
            {"$sort": {"total_weight": -1}},
            {"$limit": top_n + len(exclude_ids)}
        ]
        
        hot_course_ids = []
        async for doc in self.collection.aggregate(pipeline):
            course_id = doc["_id"]
            if course_id not in exclude_ids:
                hot_course_ids.append(course_id)
                if len(hot_course_ids) >= top_n:
                    break
        
        # 如果热度数据不足，从数据库获取最新课程
        if len(hot_course_ids) < top_n:
            query = MedicalCourse.filter(status=1, sale_status=1, is_deleted=False)
            if exclude_ids:
                query = query.exclude(id__in=exclude_ids + hot_course_ids)
            latest_courses = await query.order_by("-created_time").limit(top_n - len(hot_course_ids))
            hot_course_ids.extend([c.id for c in latest_courses])
        
        # 获取课程详情
        recommendations = []
        for course_id in hot_course_ids[:top_n]:
            course = await MedicalCourse.get_or_none(id=course_id)
            if course:
                recommendations.append({
                    "course_id": course.id,
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "medical_department": course.medical_department,
                    "difficulty_level": course.difficulty_level,
                    "price": float(course.price),
                    "recommendation_score": 0.0,
                    "recommendation_reason": "热门课程"
                })
        
        return recommendations


# 全局推荐器实例
item_cf_recommender = ItemBasedCFRecommender()
