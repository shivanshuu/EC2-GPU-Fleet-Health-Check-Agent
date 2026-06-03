from uuid import UUID

from app.models import Item


class InMemoryItemStore:
    def __init__(self) -> None:
        self._items: dict[UUID, Item] = {}

    async def create(self, item: Item) -> Item:
        self._items[item.id] = item
        return item

    async def get(self, item_id: UUID) -> Item | None:
        return self._items.get(item_id)


item_store = InMemoryItemStore()
