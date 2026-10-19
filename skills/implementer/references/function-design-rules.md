# 函数的设计规则

## 公有接口设计规范

公有接口必须遵循以下设计规范：

1. 入参类型可以相对宽松，但不能无边界。
2. 必须完成黑盒校验。
3. 必须将宽松入参转换为严格内部结构。
4. 不得在公有接口中直接编写完整业务逻辑。
5. 公有接口应调用对应的公有函数或私有函数执行实际业务。
6. 校验失败必须返回明确错误，不得进入内部逻辑。
7. 公有接口的实现必须依赖公有函数或私有函数，不能绕过内部层级直接写业务细节。

## 伪代码实例

```python
# 公有接口：仅供外部调用，负责校验与适配
def public_create_order(request: CreateOrderRequest) -> Result[OrderResponse, Error]:
    # 1. 黑盒校验
    validate(request)

    # 2. 转换为内部严格结构
    command = to_create_order_command(request)

    # 3. 调用内部业务函数
    return internal_create_order(command)


# 公有函数：项目内全局可见，但不供外部调用
def internal_create_order(command: CreateOrderCommand) -> Result[OrderResponse, Error]:
    # 白盒断言：内部契约保护
    assert command is not None  # 非空
    assert command.user_id != ""  # 用户 ID 非空
    assert len(command.items) > 0  # 条目数大于 0

    # 业务流程编排
    order = build_order(command)
    save_order(order)
    return to_order_response(order)


# 私有函数：只在自己包内可见
def build_order(command: CreateOrderCommand) -> Order:
    # 假设 command 已经通过校验
    return Order(
        user_id=command.user_id,
        items=command.items,
        status=OrderStatus.CREATED,
    )
```

## 校验规则

| 层级 | 校验类型 | 示例内容 |
| --- | --- | --- |
| 公有接口 | 黑盒校验 | 必填、类型、格式、范围、枚举、长度、字段冲突 |
| 公有函数 | 白盒断言 | 非空、状态合法、内部 DTO 已转换、依赖已初始化 |
| 私有函数 | 不重复校验 | 仅声明前置条件，如「入参必须满足 XX 条件」 |
