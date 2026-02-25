-- AgenticMCP PostgreSQL initialization script
-- This script creates sample tables and data for testing

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    name TEXT NOT NULL,
    tenant_id INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    tenant_id INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    status TEXT DEFAULT 'pending',
    total DECIMAL(10, 2) DEFAULT 0,
    tenant_id INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value DECIMAL(10, 2),
    tenant_id INTEGER DEFAULT 1,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (email, phone, name, tenant_id) VALUES
    ('alice@example.com', '+1234567890', 'Alice Johnson', 1),
    ('bob@example.com', '+0987654321', 'Bob Smith', 1),
    ('charlie@example.com', '+1122334455', 'Charlie Brown', 2),
    ('diana@example.com', '+5566778899', 'Diana Prince', 2);

INSERT INTO products (name, description, price, stock, tenant_id) VALUES
    ('Laptop', 'High-performance laptop', 1299.99, 50, 1),
    ('Mouse', 'Wireless mouse', 29.99, 200, 1),
    ('Keyboard', 'Mechanical keyboard', 89.99, 100, 1),
    ('Monitor', '27-inch 4K monitor', 399.99, 75, 1),
    ('Headphones', 'Noise-cancelling headphones', 199.99, 60, 2),
    ('Webcam', 'HD webcam', 79.99, 150, 2);

INSERT INTO orders (user_id, status, total, tenant_id) VALUES
    (1, 'completed', 1329.98, 1),
    (1, 'pending', 89.99, 1),
    (2, 'completed', 399.99, 1),
    (3, 'shipped', 279.98, 2),
    (4, 'pending', 199.99, 2);

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
    (1, 1, 1, 1299.99),
    (1, 2, 1, 29.99),
    (2, 3, 1, 89.99),
    (3, 4, 1, 399.99),
    (4, 5, 1, 199.99),
    (4, 6, 1, 79.99),
    (5, 5, 1, 199.99);

INSERT INTO analytics (metric_name, metric_value, tenant_id) VALUES
    ('daily_active_users', 1250.00, 1),
    ('daily_revenue', 15234.50, 1),
    ('conversion_rate', 3.2, 1),
    ('daily_active_users', 850.00, 2),
    ('daily_revenue', 8920.75, 2),
    ('conversion_rate', 2.8, 2);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_tenant ON orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_analytics_tenant ON analytics(tenant_id);

-- Grant permissions (adjust user as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
