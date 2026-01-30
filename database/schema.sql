-- Customer Support Database Schema
-- For John's Executive Assistant System

-- Customer Profiles
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT UNIQUE NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    customer_age INTEGER,
    customer_gender TEXT,
    product_purchased TEXT,
    date_of_purchase DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Support Tickets
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE NOT NULL,
    customer_id TEXT NOT NULL,
    ticket_type TEXT,
    ticket_subject TEXT,
    ticket_description TEXT,
    ticket_status TEXT,
    ticket_priority TEXT,
    ticket_channel TEXT,
    first_response_time TEXT,
    time_to_resolution TEXT,
    customer_satisfaction_rating REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_customer_id ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_ticket_status ON tickets(ticket_status);
CREATE INDEX IF NOT EXISTS idx_ticket_priority ON tickets(ticket_priority);
CREATE INDEX IF NOT EXISTS idx_ticket_type ON tickets(ticket_type);
CREATE INDEX IF NOT EXISTS idx_customer_email ON customers(customer_email);
CREATE INDEX IF NOT EXISTS idx_product_purchased ON customers(product_purchased);
