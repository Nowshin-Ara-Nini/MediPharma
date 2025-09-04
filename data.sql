-- ========== CORE PERSON/ACCOUNT BLOCK ==========
-- ERD: User (User_Id, Name, Email, Phone, Address, Password)
CREATE TABLE Users (
  user_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name           VARCHAR(120) NOT NULL,
  phone			 BIGINT UNSIGNED NOT NULL,
  email          VARCHAR(190) NOT NULL UNIQUE,
  address        VARCHAR(255),
  password_hash  VARCHAR(255) NOT NULL
    
) ENGINE=InnoDB;

-- ERD subtype: Customer (User_Id, Age)
CREATE TABLE customer (
  user_id BIGINT UNSIGNED PRIMARY KEY,
  age     TINYINT UNSIGNED,
  CONSTRAINT fk_customers_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ERD block: Doctor (Doctor_id, Doctor_Name, License_no, Education, Contact, Speciality)
CREATE TABLE doctors (
  user_id    BIGINT UNSIGNED PRIMARY KEY,
  doctor_name  VARCHAR(120) NOT NULL,
  license_no   VARCHAR(80)  NOT NULL UNIQUE,
  education    VARCHAR(120),
  contact      VARCHAR(120),
  specialty    VARCHAR(120),
  CONSTRAINT fk_customers_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ERD subtype: Pharmacist (User_Id, License_no)
CREATE TABLE pharmacists (
  user_id     BIGINT UNSIGNED PRIMARY KEY,
  license_no  VARCHAR(80) NOT NULL UNIQUE,
  CONSTRAINT fk_pharmacists_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ERD block: Company (User_Id, License_no)
-- (Modeled as its own entity; you can set user_id NULL if company is not a platform user.)
CREATE TABLE companies (
  user_id  BIGINT UNSIGNED PRIMARY KEY,
  license_no  VARCHAR(80),
  UNIQUE KEY uk_companies_license (license_no),
  CONSTRAINT fk_companies_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========== MEDICINE / INVENTORY BLOCK ==========
-- ERD: Medicine (Medicine_Id, Description, Expiry Date, Price, Name, Production Date)
CREATE TABLE medicines (
  medicine_id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(160) NOT NULL,
  description     TEXT,
  price           DECIMAL(10,2) NOT NULL CHECK (price >= 0),
  production_date DATE,
  expiry_date     DATE,
  feedback_id     BIGINT UNSIGNED NOT NULL,
  inventory_id	  BIGINT UNSIGNED NOT NULL,
  CONSTRAINT fk_medi_fb
    FOREIGN KEY (feedback_id) REFERENCES feedbacks(feedback_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT fk_medi_inv
    FOREIGN KEY (inventory_id) REFERENCES inventories(inventory_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE   
) ENGINE=InnoDB;

-- ERD: Inventory (Inventory_Id) managed by Pharmacist; Stocks (N) medicines with stock_quantity
CREATE TABLE inventories (
  inventory_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  medicine_id  BIGINT UNSIGNED NOT NULL,
  company_id   BIGINT UNSIGNED NOT NULL,
  pharmacist_id BIGINT UNSIGNED NULL, -- pharmacist user_id
  CONSTRAINT fk_inventories_medicine
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT fk_inventories_company
    FOREIGN KEY (company_id) REFERENCES companies(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_inventories_pharmacist
    FOREIGN KEY (managed_by) REFERENCES pharmacists(user_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ERD: Inventory —< Stocks >— Medicine  (with stock_quantity)
CREATE TABLE inventory_items (
  inventory_id BIGINT UNSIGNED NOT NULL,
  medicine_id  BIGINT UNSIGNED NOT NULL,
  stock_quantity INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (inventory_id, medicine_id),
  CONSTRAINT fk_inventory_items_inventory
    FOREIGN KEY (inventory_id) REFERENCES inventories(inventory_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_inventory_items_medicine
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ERD: Manufactures (M:N) Company — Medicine
CREATE TABLE company_manufactures (
  company_id  BIGINT UNSIGNED NOT NULL,
  medicine_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (company_id, medicine_id),
  CONSTRAINT fk_cm_company
    FOREIGN KEY (company_id) REFERENCES companies(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_cm_medicine
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ERD: Requests_Stock (Pharmacist — Company) (optional metadata fields)
CREATE TABLE stock_requests (
  pharmacist_id BIGINT UNSIGNED NOT NULL, -- users.user_id (pharmacist)
  company_id    BIGINT UNSIGNED NOT NULL,
  medicine_id   BIGINT UNSIGNED NULL,
  quantity      INT UNSIGNED,
  status        ENUM('pending','approved','rejected','fulfilled') DEFAULT 'pending',
  CONSTRAINT fk_sr_pharmacist
    FOREIGN KEY (pharmacist_id) REFERENCES pharmacists(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_sr_company
    FOREIGN KEY (company_id) REFERENCES companies(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_sr_medicine
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========== SHOPPING / ORDERING BLOCK ==========
-- ERD: Cart (Cart_id, Total_Amount, user_id)
CREATE TABLE carts (
  cart_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT UNSIGNED NOT NULL, -- customer
  total_amount  DECIMAL(12,2) NOT NULL DEFAULT 0,
  CONSTRAINT fk_carts_customer
    FOREIGN KEY (user_id) REFERENCES customers(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ERD: Medicines (under Cart) → this is the cart’s line items
CREATE TABLE cart_items (
  cart_id      BIGINT UNSIGNED NOT NULL,
  medicine_id  BIGINT UNSIGNED NOT NULL,
  quantity     INT UNSIGNED NOT NULL DEFAULT 1,
  CONSTRAINT fk_ci_cart
    FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_ci_medicine
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE payments (
  order_id     		BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  cart_id			BIGINT UNSIGNED NOT NULL,
  customer_id   	BIGINT UNSIGNED NOT NULL,
  time_ordered      DATE DEFAULT (CURRENT_DATE),
  method         ENUM('card','cash','wallet','bank','other') NOT NULL,
  transaction_id VARCHAR(120),
  status         ENUM('initiated','successful','failed','refunded') DEFAULT 'initiated',
  paid_on        DATE DEFAULT (CURRENT_DATE),
  CONSTRAINT fk_cart_id
    FOREIGN KEY (cart_id) REFERENCES carts(order_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ========== FEEDBACK / WISHLIST BLOCK ==========
-- ERD: Feedback (Feedback_Id, Time, Rating, Comments, Verifiedlogin_flag)
-- "Gives" (Customer → Feedback) and (Feedback → Medicine)
CREATE TABLE feedbacks (
  feedback_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  rating            TINYINT UNSIGNED NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comments          TEXT,
  time_given        DATE DEFAULT (CURRENT_DATE),
  verifiedlogin_flag BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE KEY uk_feedback_unique (customer_id, medicine_id) -- one review per customer per medicine
) ENGINE=InnoDB;

-- ERD: Wishlist (Wishlist_Id, Product_status, User_Id) and Items (Wishlist_Id, Item)
CREATE TABLE wishlists (
  wishlist_id    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id        BIGINT UNSIGNED NOT NULL,
  product_status BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT fk_wishlists_user
    FOREIGN KEY (user_id) REFERENCES customers(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE wishlist_items (
  wishlist_id BIGINT UNSIGNED NOT NULL,
  wishlist_item BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (wishlist_id, medicine_id),
  CONSTRAINT fk_wli_wishlist
    FOREIGN KEY (wishlist_id) REFERENCES wishlists(wishlist_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
) ENGINE=InnoDB;

-- ========== APPOINTMENTS BLOCK ==========
-- ERD: Appoints (Customer ↔ Doctor) with scheduled_at, appointment_id, Note
CREATE TABLE appointments (
  appointment_id BIGINT UNSIGNED NOT NULL,
  customer_id    BIGINT UNSIGNED NOT NULL,
  doctor_id      BIGINT UNSIGNED NOT NULL,
  scheduled_at   DATETIME NOT NULL,
  note           TEXT,
  CONSTRAINT fk_appt_customer
    FOREIGN KEY (customer_id) REFERENCES customers(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_appt_doctor
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  UNIQUE KEY uk_appt_unique (doctor_id, scheduled_at)
) ENGINE=InnoDB;

-- ========== ADMIN PANEL BLOCK ==========
-- ERD: Admin Panel (Admin_Id, User_Id)
CREATE TABLE admins (
  user_id  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  CONSTRAINT fk_admins_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

