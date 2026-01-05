# test_install.py
try:
    from elasticsearch_dsl import Document, Text, Keyword, Integer, Date, Object, Boolean

    print("✅ 成功导入 elasticsearch_dsl.Document")


    class MyDoc(Document):
        title = Text()


    print("✅ 成功定义 Document 模型")

except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确认你运行此脚本的 Python 环境安装了 elasticsearch-dsl")
except Exception as e:
    print(f"❌ 其他错误: {e}")