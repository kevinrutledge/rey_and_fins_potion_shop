-- Customers Table
CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    visit_id BIGINT REFERENCES visits(visit_id),
    customer_name VARCHAR NOT NULL,
    character_class VARCHAR NOT NULL,
    level INT NOT NULL
);

-- Carts Table
CREATE TABLE carts (
    cart_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT REFERENCES customers(customer_id),
    created_at TIMESTAMPTZ NOT NULL,
    checked_out BOOLEAN DEFAULT FALSE,
    total_potions_bought INT DEFAULT 0,
    total_gold_paid INT DEFAULT 0,
    payment VARCHAR
);

-- Cart Items Table
CREATE TABLE cart_items (
    cart_item_id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT REFERENCES carts(cart_id),
    potion_id INT REFERENCES potions(potion_id),
    quantity INT NOT NULL,
    price INT NOT NULL,
    line_item_total INT NOT NULL
);

-- Potions Table
CREATE TABLE potions (
    potion_id BIGSERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    sku VARCHAR NOT NULL UNIQUE,
    red_ml INT NOT NULL,
    green_ml INT NOT NULL,
    blue_ml INT NOT NULL,
    dark_ml INT NOT NULL,
    total_ml INT NOT NULL,
    price INT NOT NULL,
    description TEXT,
    current_quantity INT NOT NULL
);

-- Global Inventory Table
CREATE TABLE global_inventory (
    id BIGINT PRIMARY KEY,
    gold INT DEFAULT 100,
    total_potions INT DEFAULT 0,
    total_ml INT DEFAULT 0,
    red_ml INT DEFAULT 0,
    green_ml INT DEFAULT 0,
    blue_ml INT DEFAULT 0,
    dark_ml INT DEFAULT 0,
    potion_capacity_units INT DEFAULT 1,
    ml_capacity_units INT DEFAULT 1
);

-- Visits Table
CREATE TABLE visits (
    visit_id BIGSERIAL PRIMARY KEY,
    visit_time TIMESTAMPTZ NOT NULL
);

-- Ledger Entries Table
CREATE TABLE ledger_entries (
    ledger_entry_id BIGSERIAL PRIMARY KEY,
    change_type VARCHAR NOT NULL,
    sub_type VARCHAR,
    amount INT NOT NULL,
    ml_type VARCHAR,
    potion_id INT REFERENCES potions(potion_id),
    description TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);