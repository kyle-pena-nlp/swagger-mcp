from fastapi import FastAPI, HTTPException, Depends, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
import uvicorn
import os
from datetime import datetime
from contextlib import asynccontextmanager

from sample_rest_api.app.database import database, create_tables, categories, products
from sample_rest_api.app.seed import seed_data
from sample_rest_api.app.logger import logger


def get_port():
    return int(os.environ.get("API_PORT", 9000))

# Create FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up")
    logger.info("Creating database tables")
    create_tables()
    logger.info("Connecting to database")
    await database.connect()
    logger.info("Database connection established")
    logger.info("Seeding initial data")
    await seed_data()
    logger.info("Application startup completed")
    logger.info(f"---> http://localhost:{get_port()}/docs <---")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")
    logger.info("Disconnecting from database")
    await database.disconnect()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="Product-Category API",
    description="A simple REST API for managing products and categories - a sample server for SwaggerMCP! Follow the README to integrate with your favorite IDE.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class CategoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

class ProductBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: Optional[str] = None
    price: float
    category_id: str
    in_stock: bool = True

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

class SearchResults(BaseModel):
    products: List[Product]
    total_count: int
    search_metadata: dict

# CRUD Operations for Categories
@app.post("/categories/", response_model=Category, status_code=201, tags=["categories"])
async def create_category(category: CategoryCreate):
    """
    Create a new category with the given details
    """
    logger.info(f"Creating new category: {category.name}")
    now = datetime.utcnow()
    category_id = str(uuid.uuid4())
    query = categories.insert().values(
        id=category_id,
        name=category.name,
        description=category.description,
        created_at=now,
        updated_at=now
    )
    await database.execute(query)
    category_data = category.model_dump()
    return {**category_data, "id": category_id, "created_at": now, "updated_at": now}

@app.get("/categories/", response_model=List[Category], tags=["categories"])
async def list_categories(skip: int = 0, limit: int = 100):
    """
    Retrieve all categories with pagination
    """
    logger.info(f"Listing categories with skip={skip}, limit={limit}")
    query = categories.select().offset(skip).limit(limit)
    result = await database.fetch_all(query)
    logger.info(f"Retrieved {len(result)} categories")
    return result

@app.get("/categories/{category_id}", response_model=Category, tags=["categories"])
async def read_category(category_id: str):
    """
    Get a specific category by ID
    """
    logger.info(f"Fetching category with ID: {category_id}")
    query = categories.select().where(categories.c.id == category_id)
    db_category = await database.fetch_one(query)
    
    if db_category is None:
        logger.warning(f"Category not found with ID: {category_id}")
        raise HTTPException(status_code=404, detail="Category not found")
    
    logger.info(f"Successfully retrieved category: {db_category['name']}")
    return db_category

@app.put("/categories/{category_id}", response_model=Category, tags=["categories"])
async def update_category(category_id: str, category: CategoryCreate):
    """
    Update a category with the given details
    """
    logger.info(f"Updating category with ID: {category_id}")
    # Check if category exists
    query = categories.select().where(categories.c.id == category_id)
    db_category = await database.fetch_one(query)
    
    if db_category is None:
        logger.warning(f"Attempted to update non-existent category with ID: {category_id}")
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update category
    now = datetime.utcnow()
    query = categories.update().where(categories.c.id == category_id).values(
        **category.model_dump(),
        updated_at=now
    )
    await database.execute(query)
    logger.info(f"Category updated successfully: {category.name}")
    
    # Get updated category
    query = categories.select().where(categories.c.id == category_id)
    return await database.fetch_one(query)

@app.delete("/categories/{category_id}", status_code=204, tags=["categories"])
async def delete_category(category_id: str):
    """
    Delete a category by ID
    """
    logger.info(f"Deleting category with ID: {category_id}")
    # Check if category exists
    query = categories.select().where(categories.c.id == category_id)
    db_category = await database.fetch_one(query)
    
    if db_category is None:
        logger.warning(f"Attempted to delete non-existent category with ID: {category_id}")
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if any products are using this category
    query = products.select().where(products.c.category_id == category_id)
    db_products = await database.fetch_all(query)
    
    if len(db_products) > 0:
        logger.warning(f"Cannot delete category ID: {category_id} as it has {len(db_products)} products assigned")
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category that has products assigned to it"
        )
    
    # Delete category
    query = categories.delete().where(categories.c.id == category_id)
    await database.execute(query)
    logger.info(f"Category deleted successfully: {db_category['name']}")
    
    return None

# CRUD Operations for Products
@app.post("/products/", response_model=Product, status_code=201, tags=["products"])
async def create_product(product: ProductCreate):
    """
    Create a new product with the given details
    """
    logger.info(f"Creating new product: {product.name}")
    # Check if category exists
    query = categories.select().where(categories.c.id == product.category_id)
    db_category = await database.fetch_one(query)
    
    if db_category is None:
        logger.warning(f"Attempted to create product with non-existent category ID: {product.category_id}")
        raise HTTPException(status_code=400, detail="Category not found")
    
    product_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    query = products.insert().values(
        id=product_id,
        name=product.name,
        description=product.description,
        price=product.price,
        category_id=product.category_id,
        in_stock=product.in_stock,
        created_at=now,
        updated_at=now
    )
    
    await database.execute(query)
    logger.info(f"Product created successfully with ID: {product_id}")
    
    return {**product.model_dump(), "id": product_id, "created_at": now, "updated_at": now}

@app.get("/products/", response_model=List[Product], tags=["products"])
async def list_products(
    skip: int = 0, 
    limit: int = 100,
    category_id: Optional[str] = None,
    in_stock: Optional[bool] = None
):
    """
    Retrieve all products with optional filtering by category and stock status
    """
    log_msg = f"Listing products with skip={skip}, limit={limit}"
    if category_id:
        log_msg += f", category_id={category_id}"
    if in_stock is not None:
        log_msg += f", in_stock={in_stock}"
    logger.info(log_msg)
    
    query = products.select()
    
    if category_id:
        query = query.where(products.c.category_id == category_id)
    
    if in_stock is not None:
        query = query.where(products.c.in_stock == in_stock)
    
    query = query.offset(skip).limit(limit)
    result = await database.fetch_all(query)
    logger.info(f"Retrieved {len(result)} products")
    return result

@app.get("/products/{product_id}", response_model=Product, tags=["products"])
async def read_product(product_id: str):
    """
    Get a specific product by ID
    """
    logger.info(f"Fetching product with ID: {product_id}")
    query = products.select().where(products.c.id == product_id)
    db_product = await database.fetch_one(query)
    
    if db_product is None:
        logger.warning(f"Product not found with ID: {product_id}")
        raise HTTPException(status_code=404, detail="Product not found")
    
    logger.info(f"Successfully retrieved product: {db_product['name']}")
    return db_product

@app.put("/products/{product_id}", response_model=Product, tags=["products"])
async def update_product(product_id: str, product: ProductCreate):
    """
    Update a product with the given details
    """
    logger.info(f"Updating product with ID: {product_id}")
    # Check if product exists
    query = products.select().where(products.c.id == product_id)
    db_product = await database.fetch_one(query)
    
    if db_product is None:
        logger.warning(f"Attempted to update non-existent product with ID: {product_id}")
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if category exists
    query = categories.select().where(categories.c.id == product.category_id)
    db_category = await database.fetch_one(query)
    
    if db_category is None:
        logger.warning(f"Attempted to update product with non-existent category ID: {product.category_id}")
        raise HTTPException(status_code=400, detail="Category not found")
    
    # Update product
    now = datetime.utcnow()
    query = products.update().where(products.c.id == product_id).values(
        **product.model_dump(),
        updated_at=now
    )
    
    await database.execute(query)
    logger.info(f"Product updated successfully: {product.name}")
    
    # Get updated product
    query = products.select().where(products.c.id == product_id)
    return await database.fetch_one(query)

@app.delete("/products/{product_id}", status_code=204, tags=["products"])
async def delete_product(product_id: str):
    """
    Delete a product by ID
    """
    logger.info(f"Deleting product with ID: {product_id}")
    # Check if product exists
    query = products.select().where(products.c.id == product_id)
    db_product = await database.fetch_one(query)
    
    if db_product is None:
        logger.warning(f"Attempted to delete non-existent product with ID: {product_id}")
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete product
    query = products.delete().where(products.c.id == product_id)
    await database.execute(query)
    logger.info(f"Product deleted successfully: {db_product['name']}")
    
    return None

@app.post("/products/search/{category_id}", response_model=SearchResults, tags=["products"])
async def search_products(
    category_id: str,  # path parameter
    query: str = Query(None, description="Search term for product name/description"),  # query parameter
    min_price: float = Query(None, ge=0),  # query parameter with validation
    max_price: float = Query(None, ge=0),  # query parameter with validation
    sort_by: str = Form(...),  # form field
    sort_order: str = Form(default="asc", pattern="^(asc|desc)$"),  # form field with validation
    page: int = Query(1, ge=1),  # query parameter with validation
    items_per_page: int = Query(10, ge=1, le=100)  # query parameter with validation
):
    """
    Search for products using multiple parameter types:
    - Path parameter for category
    - Query parameters for search term and price range
    - Form data for sorting options
    - Pagination parameters
    """
    logger.info(f"Searching products in category {category_id}")
    
    # Validate category exists
    category_query = categories.select().where(categories.c.id == category_id)
    if not await database.fetch_one(category_query):
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Build base query
    query_filters = [products.c.category_id == category_id]
    if query:
        query_filters.append(
            (products.c.name.ilike(f"%{query}%")) | 
            (products.c.description.ilike(f"%{query}%"))
        )
    if min_price is not None:
        query_filters.append(products.c.price >= min_price)
    if max_price is not None:
        query_filters.append(products.c.price <= max_price)
    
    # Count total results
    count_query = products.select().where(*query_filters)
    total_count = len(await database.fetch_all(count_query))
    
    # Add sorting
    order_by = getattr(products.c, sort_by, products.c.name)
    if sort_order == "desc":
        order_by = order_by.desc()
    
    # Add pagination
    offset = (page - 1) * items_per_page
    
    # Final query
    final_query = (
        products.select()
        .where(*query_filters)
        .order_by(order_by)
        .offset(offset)
        .limit(items_per_page)
    )
    
    results = await database.fetch_all(final_query)
    
    search_metadata = {
        "page": page,
        "items_per_page": items_per_page,
        "total_pages": (total_count + items_per_page - 1) // items_per_page,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "filters_applied": {
            "query": query,
            "min_price": min_price,
            "max_price": max_price
        }
    }
    
    logger.info(f"Found {total_count} products matching search criteria")
    return {
        "products": results,
        "total_count": total_count,
        "search_metadata": search_metadata
    }


if __name__ == "__main__":
    port = get_port()
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 