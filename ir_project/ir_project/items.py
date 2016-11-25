from scrapy.item import Item, Field

class IrProjectItem(Item):
	url = Field()
	title = Field()
	body = Field()
	body2 = Field()
	pass
