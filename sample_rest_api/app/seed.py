import uuid
from datetime import datetime
from sample_rest_api.app.database import database, categories, products
from sample_rest_api.app.logger import logger

# Sample data for seeding the database
sample_categories = [
    {
        "id": str(uuid.uuid4()),
        "name": "Electronics",
        "description": "Electronic devices and gadgets",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Books",
        "description": "Physical and digital books",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Clothing",
        "description": "Apparel and fashion items",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

# We'll populate sample products after categories are created
async def get_sample_products():
    # Get all category IDs from the database
    query = categories.select()
    db_categories = await database.fetch_all(query)
    category_ids = [category["id"] for category in db_categories]
    
    if len(category_ids) < 3:
        return []
    
    # Create sample products with valid category IDs
    return [
        {
            "id": str(uuid.uuid4()),
            "name": "Smartphone",
            "description": "Latest model smartphone with advanced features",
            "price": 799.99,
            "category_id": category_ids[0],  # Electronics
            "in_stock": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Laptop",
            "description": "High-performance laptop for work and gaming",
            "price": 1299.99,
            "category_id": category_ids[0],  # Electronics
            "in_stock": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Novel",
            "description": "Bestselling fiction novel",
            "price": 24.99,
            "category_id": category_ids[1],  # Books
            "in_stock": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "T-Shirt",
            "description": "Cotton t-shirt with graphic design",
            "price": 19.99,
            "category_id": category_ids[2],  # Clothing
            "in_stock": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Jeans",
            "description": "Classic blue jeans",
            "price": 49.99,
            "category_id": category_ids[2],  # Clothing
            "in_stock": False,  # Out of stock example
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]

async def seed_data():
    # Check if database is already populated
    query = categories.select()
    existing_categories = await database.fetch_all(query)
    
    if existing_categories:
        logger.info("Database already has data, skipping seed")
        return
    
    logger.info("Seeding database with initial data...")
    
    # Insert categories
    for category in sample_categories:
        query = categories.insert().values(**category)
        await database.execute(query)
    
    # Insert products
    sample_products = await get_sample_products()
    for product in sample_products:
        query = products.insert().values(**product)
        await database.execute(query)
    
    logger.info("Database seeded successfully!") 