# -*- coding: utf-8 -*-
import scrapy
import json
import requests
from dotenv import load_dotenv
import os
load_dotenv()

"""
TODO
-remove product if it's no longer available (maybe just remove it if it hasn't been updated in a while
"""
def getItemInfo(response):
    script= response.xpath("//div[@class='container-fluid product-details-wrapper']/script").get()
    #script = script.replace("\n", "")
    script = script.replace("<script type=\"application/ld+json\">", "")
    script = script.replace("</script>", "")
    scriptJson = json.loads(script)
    return (scriptJson["name"], scriptJson["offers"]["price"], scriptJson["offers"]["availability"], scriptJson["image"][0])
def getDescription(response):
    return response.xpath("//div[@class='content-detail']").get()
def getCollection(response):
    collectionDict = {
            'Beverages': 238417445058,
            'Bread & Bakery': 238417477826,
            'Breakfast & Cereal':238417543362,
            'Canned Goods & Soups': 238417576130,
            'Condiments, Spice & Bake':238417608898,
            'Cookies, Snacks & Candy': 238417674434,
            'Dairy, Eggs & Cheese': 238417707202,
            'Deli': 242397642946,
            'Frozen Foods': 238423048386,
            'Fruits & Vegetables': 238417772738,
            'Grains, Pasta & Sides': 238417805506,
            'International Cuisine': 242059247810,
            'Meat & Seafood': 238417838274,
            'Paper, Cleaning & Home': 242312020162,
            }
    collectionText = response.xpath("//ul[@class='nav nav-Crumb']/li[2]/a/text()").get()
    return collectionDict[collectionText]
def getTags(response):
    i = 3
    tag = ''
    while response.xpath("//ul[@class='nav nav-Crumb']/li[%i]/a/text()" % i) != []:
        tag = response.xpath("//ul[@class='nav nav-Crumb']/li[%i]/a/text()" % i).get().replace(',', ' ')
        i+=1
    
    return tag
def generateProductJSON(name, price, availability, image, tags = '', description = ''):
    return {
      "product": {
        "title": name,
        "body_html": description,
        "vendor": "pavilions",
        "tags": tags,
        "variants":[
            {
                "title": "Default Title",
                "price": str(price),
                "fulfillment_service": "manual",
                "taxable": "false",
                "requires_shipping": "false",
            }
        ],
        "images": [
            {
                "src": image,
            },
        ],
        },
    }

def generateCollectJSON(collection_id, product_id):
    return {
          "collect": {
            "product_id": product_id,
            "collection_id": collection_id,
          },
        }
def getPrevProducts(productUrl):
    prevProducts = {}
    links = set()
    x = requests.get(productUrl + "?fields=id,title,variants,tags&limit=250")
    #case1: no products
    if x.text == '{"products":[]}': return {}
    for product in json.loads(x.text)["products"]:
            prevProducts[product['title']] = {
                'id': product['id'],
                'price': product['variants'][0]['price'],
                'variant_id': product['variants'][0]['id'],
                'tags': product['tags']}
    #case2: only one page of products
    if 'Link' not in x.headers: return prevProducts
    #case 3: multiple pages of products
    else:
        while True:
            nextLink = productUrl + "?fields=id,title,variants,tags&limit=250&" + x.headers['Link'][x.headers['Link'].rindex('page_info'): x.headers['Link'].rindex('>')]
            if nextLink in links:
                return prevProducts
            links.add(nextLink)
            x = requests.get(nextLink)
            for product in json.loads(x.text)["products"]:
                prevProducts[product['title']] = {
                    'id': product['id'],
                    'price': product['variants'][0]['price'],
                    'variant_id': product['variants'][0]['id'],
                    'tags': product['tags']
                    }
    
class PavilionsSpider(scrapy.Spider):
    name = 'pavilions'
    allowed_domains = ['pavilions.com']
    custom_settings = { 'LOG_LEVEL': 'INFO',
                        'ADD_NEW_PRODUCTS': True,
                        'UPDATE_PRODUCTS': True}
    
    user = os.getenv('user')
    password = os.getenv('password')
    shop = "curbongroceries.myshopify.com"
    productPath = "/admin/api/2021-01/products.json"
    collectPath = "/admin/api/2021-01/collects.json"
    productUrl = "https://" + user + ":" + password + "@" + shop + productPath
    collectUrl = "https://" + user + ":" + password + "@" + shop + collectPath
    urls = []
    #the basics
    urls += ['https://www.pavilions.com/shop/aisles/beverages.2739.html',
            'https://www.pavilions.com/shop/aisles/bread-bakery.2739.html',
            'https://www.pavilions.com/shop/aisles/breakfast-cereal.2739.html',
            'https://www.pavilions.com/shop/aisles/canned-goods-soups.2739.html',
            'https://www.pavilions.com/shop/aisles/condiments-spice-bake.2739.html',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy.2739.html',
            'https://www.pavilions.com/shop/aisles/dairy-eggs-cheese.2739.html',
            'https://www.pavilions.com/shop/aisles/frozen-foods.2739.html',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables.2739.html',
            'https://www.pavilions.com/shop/aisles/grains-pasta-sides.2739.html',
            'https://www.pavilions.com/shop/aisles/international-cuisine.2739.html',
            'https://www.pavilions.com/shop/aisles/meat-seafood.2739.html',
            'https://www.pavilions.com/shop/aisles/paper-cleaning-home.2739.html',
            'https://www.pavilions.com/shop/aisles/deli.2739.html',
            ]
    #types of products that i want to get more variety of
    urls += ['https://www.pavilions.com/shop/aisles/beverages/coffee.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/beverages/tea.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/beverages/soft-drinks.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/bread-bakery/sandwich-breads.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/breakfast-cereal/cereal.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/condiments-spice-bake/baking-ingredients.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/condiments-spice-bake/baking-ingredients.2739.html?sort=&page=3',
            'https://www.pavilions.com/shop/aisles/condiments-spice-bake/jam-spreads-condiments.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/dairy-eggs-cheese/cheese.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/frozen-foods/frozen-vegetables.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/frozen-foods/frozen-meals-sides.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/fresh-fruits.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/fresh-vegetables-herbs.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/grains-pasta-sides/pasta.2739.html?page=1&sort=&brand=Rana~Barilla',
            'https://www.pavilions.com/shop/aisles/international-cuisine/hispanic-foods.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/condiments-spice-bake/baking-dough-mixes.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/condiments-spice-bake/baking-dough-mixes.2739.html?sort=&page=3',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy/chips.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy/chocolate.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/packaged-produce.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/packaged-produce/tofu-meat-alternatives.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/fresh-vegetables-herbs.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/deli/deli-cheese.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy/chips/tortilla-chips.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy/chips/potato-chips-crisps.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy/chocolate/chocolate.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy/chocolate/chocolate.2739.html?sort=&page=3',
            'https://www.pavilions.com/shop/search-results.html?q=plant%20based%20meat',
            'https://www.pavilions.com/shop/aisles/condiments-spice-bake/baking-dough-mixes/rolls-pastry-dough.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/fresh-vegetables-herbs/mushrooms.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/international-cuisine/asian-foods/asian-specialty-foods.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/frozen-foods/frozen-meals-sides/frozen-pizza-multi-serve.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/meat-seafood/fish-shellfish/smoked-cured-fish.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/deli/deli-cheese/feta-cheese.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/deli/deli-cheese/parmesan-asiago-cheese.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/deli/deli-cheese/cheddar-jack-cheese.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy/chips/potato-chips-crisps.2739.html?sort=&page=1',
            'https://www.pavilions.com/shop/aisles/cookies-snacks-candy/chocolate/chocolate.2739.html?sort=&page=3',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/fresh-vegetables-herbs.2739.html?sort=&page=3',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/fresh-vegetables-herbs.2739.html?sort=&page=5',
            'https://www.pavilions.com/shop/aisles/fruits-vegetables/fresh-fruits.2739.html?sort=&page=3',
            ]
    #beyond meat products
    urls += ['https://www.pavilions.com/shop/product-details.960494307.html',
            'https://www.pavilions.com/shop/product-details.960461658.html',
            'https://www.pavilions.com/shop/product-details.960526235.html',
            'https://www.pavilions.com/shop/product-details.960295568.html',
            'https://www.pavilions.com/shop/product-details.970002916.html',
            'https://www.pavilions.com/shop/product-details.960565723.html',
            'https://www.pavilions.com/shop/product-details.960568256.html',
            ]
    #yellow rice
    urls += ['https://www.pavilions.com/shop/product-details.126150032.html',
            'https://www.pavilions.com/shop/product-details.960152021.html',]
    prevProducts = getPrevProducts(productUrl)
    #kinda confusing but it gets all the products from the db, creates a dict with key of product title
    #value is dict of id and price
    print("Number of previous products: %i" % len(prevProducts))
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback = self.parse)
    def parse(self, response): 
        if "product-details" in response.url:
            #if item is not available, getItemInfo fails
            try: (name, price, availability, image) = getItemInfo(response)
            except: return
            #if item is in collection that I don't want (cigarettes for example), getCollection fails
            try: collectionID = getCollection(response)
            except: return
            tags = getTags(response)
            if name in self.prevProducts and self.custom_settings['UPDATE_PRODUCTS']:
                self.logger.info("Already seen product: %s" % name)
                if float(self.prevProducts[name]['price']) == float(price) and self.prevProducts[name]['tags'] == tags: return
                else:
                    updatedProduct = {'product': {
                        'id': self.prevProducts[name]['id'],
                        'tags': tags,
                        'vendor': 'pavilions',
                        'variants':[
                                {
                                    'id': self.prevProducts[name]['variant_id'],
                                    'price': str(price),
                                }]}}
                    p = requests.put(self.productUrl[:-5] + '/%i' % self.prevProducts[name]['id'] + '.json', json=updatedProduct)
                    self.logger.info('Updating item of %s from %s to %s, tags are %s' % (name, self.prevProducts[name]['price'], price, tags))
            elif self.custom_settings['ADD_NEW_PRODUCTS']:
                p = requests.post(self.productUrl, json=generateProductJSON(name, price, availability, image, getTags(response)))
                p = json.loads(p.text)
                self.logger.info("Adding product: %s" % name)
                productID = p["product"]["id"]
                self.prevProducts[name] = {'id': productID, 'price': price}
                collect = requests.post(self.collectUrl, json=generateCollectJSON(collectionID, productID))
        elif response.url.startswith('https://www.pavilions.com/shop'):
            self.logger.info('Non-Product url: %s' % response.url)
            for href in response.css('a::attr(href)'):
                url = response.urljoin(href.extract())
                if url.startswith('mailto'): continue
                elif (('brand=' in url) and (('~' in url) or ('%7E' in url))): continue
                yield scrapy.Request(url, callback = self.parse)


