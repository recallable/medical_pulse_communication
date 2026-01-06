from typing import overload

@overload
def test_overload(a: int, b: int) -> int: ...

@overload
def test_overload(a: str, b: str) -> str: ...


def test_overload(a, b):
    """
    测试重载函数
    """
    return a + b

if __name__ == "__main__":
    print(test_overload(1, 2))
    print(test_overload("a", "b"))