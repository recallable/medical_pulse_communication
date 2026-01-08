我将按照您的要求，将 MongoDB 数据模型定义在 `models/document` 目录下，并实现课程评价功能。

### 计划内容

1. **定义 Document 模型 (`models/document/comment.py`)**:

   * 创建 `CourseComment` 类（继承 Pydantic `BaseModel`），作为 MongoDB 的文档结构定义。

   * 字段包括：`course_id`, `user_id`, `username`, `user_avatar` (冗余存储以提升查询效率), `rating`, `tags`, `content`, `created_at`。

2. **定义 Schema 模型 (`models/schemas/comment.py`)**:

   * 创建 `CommentCreate`: 用于前端请求，包含 `course_id`, `rating`, `tags`, `content` (限制 300 字)。

   * 创建 `CommentResponse`: 用于 API 响应。

3. **扩展 MongoDB 初始化 (`core/mongodb_client.py`)**:

   * 在 `_create_indexes` 中为 `course_comments` 集合添加索引：

     * `course_id` (升序，用于查询列表)

     * `created_at` (降序，用于最新排序)

4. **实现业务逻辑 (`services/comment_service.py`)**:

   * `create_comment`: 组装 `CourseComment` 文档并插入 MongoDB。

   * `get_comments`: 查询指定课程的评论列表，支持分页。

5. **实现 API 接口 (`api/course/comment.py`)**:

   * `POST /api/v1/course/comment`: 发布评论。

   * `GET /api/v1/course/{course_id}/comments`: 获取评论列表。

6. **注册路由 (`api/router.py`)**:

   * 注册新的评论路由模块。

### 预期效果

代码结构将严格遵循项目规范，将 MongoDB 文档定义与 API 交互模型分离，同时实现高性能的评论存储与查询。
