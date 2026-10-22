# 方法间的调用规则

编写方法间的调用时，先判断两个方法所处的模块与层次，再选择调用方式。

## 场景与推荐方式

| 场景 | 推荐方式 | 说明 |
| --- | --- | --- |
| 同一模块内 | 可以直接调用 | 属于内部实现细节，不需要过度抽象 |
| 模块内跨层 | 优先通过接口 / 抽象调用 | 比如 Service 调用 Repository，避免 Service 直接依赖具体实现 |
| 不同模块间 | 通过公共接口 + DI | 调用方依赖接口，提供方实现接口，由容器注入 |
| 模块边界 | 禁止跨模块直接引用实现类 | 否则模块边界会被悄悄破坏 |

## 必要约束

1. **不要为了 DI 而 DI**：如果两个类本来就在同一个模块、职责紧密，直接调用反而更清晰。
2. **DI 注入的应该是抽象，而不是具体实现类**。
3. 不同模块间调用时，调用方只依赖提供方暴露的公共接口，不得引用其实现类、内部数据结构或私有函数。
4. 同一模块内跨层调用时，接口 / 抽象在本模块内定义，避免上层直接依赖下层的具体实现。

## 判断顺序

1. 两个方法是否属于同一模块？
   - 否 → 提供方实现公共接口，调用方依赖该接口，由容器注入。
2. 是 → 是否处于不同层？
   - 否 → 直接调用。
   - 是 → 是否会替换实现或需要隔离依赖？是则通过接口 / 抽象调用，否则直接调用。

## 正例与反例

```python
# 反例：跨模块直接引用实现类，模块边界被破坏
from order_module.repository.order_repository_impl import OrderRepositoryImpl


class OrderService:
    def __init__(self):
        self.repo = OrderRepositoryImpl()  # 直接依赖具体实现


# 正例：跨模块依赖公共接口，由容器注入抽象
from order_module.api import OrderRepository  # 提供方暴露的公共接口


class OrderService:
    def __init__(self, repo: OrderRepository):  # 注入的是抽象
        self.repo = repo


# 正例：同一模块内职责紧密，直接调用
class OrderHandler:
    def create_order(self, command):
        return build_order(command)  # 同模块私有函数，直接调用即可
```
