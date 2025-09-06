SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";




CREATE TABLE `admins` (
  `user_id` bigint(20) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `appointments` (
  `appointment_id` bigint(20) UNSIGNED NOT NULL,
  `customer_id` bigint(20) UNSIGNED NOT NULL,
  `doctor_id` bigint(20) UNSIGNED NOT NULL,
  `scheduled_at` datetime NOT NULL,
  `patient_records` varchar(255) DEFAULT NULL,
  `prescriptions` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `carts` (
  `cart_id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `total_amount` decimal(12,2) NOT NULL DEFAULT 0.00,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `cart_items` (
  `cart_id` bigint(20) UNSIGNED NOT NULL,
  `medicine_id` bigint(20) UNSIGNED NOT NULL,
  `quantity` int(10) UNSIGNED NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `companies` (
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `license_no` varchar(80) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `company_manufactures` (
  `company_id` bigint(20) UNSIGNED NOT NULL,
  `medicine_id` bigint(20) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `customer` (
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `age` tinyint(3) UNSIGNED DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `doctors` (
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `doctor_name` varchar(120) NOT NULL,
  `license_no` varchar(80) NOT NULL,
  `education` varchar(120) DEFAULT NULL,
  `contact` varchar(120) DEFAULT NULL,
  `specialty` varchar(120) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `feedbacks` (
  `feedback_id` bigint(20) UNSIGNED NOT NULL,
  `customer_id` bigint(20) UNSIGNED NOT NULL,
  `medicine_id` bigint(20) UNSIGNED NOT NULL,
  `rating` tinyint(3) UNSIGNED NOT NULL CHECK (`rating` between 1 and 5),
  `comments` text DEFAULT NULL,
  `time_given` date DEFAULT curdate(),
  `verifiedlogin_flag` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `inventories` (
  `inventory_id` bigint(20) UNSIGNED NOT NULL,
  `company_id` bigint(20) UNSIGNED NOT NULL,
  `pharmacist_id` bigint(20) UNSIGNED DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `inventory_items` (
  `inventory_id` bigint(20) UNSIGNED NOT NULL,
  `medicine_id` bigint(20) UNSIGNED NOT NULL,
  `stock_quantity` int(10) UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `medicines` (
  `medicine_id` bigint(20) UNSIGNED NOT NULL,
  `name` varchar(160) NOT NULL,
  `description` text DEFAULT NULL,
  `price` decimal(10,2) NOT NULL CHECK (`price` >= 0),
  `production_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `payments` (
  `order_id` bigint(20) UNSIGNED NOT NULL,
  `cart_id` bigint(20) UNSIGNED NOT NULL,
  `customer_id` bigint(20) UNSIGNED NOT NULL,
  `time_ordered` datetime DEFAULT current_timestamp(),
  `method` enum('card','cash','wallet','bank','other') NOT NULL,
  `transaction_id` varchar(120) DEFAULT NULL,
  `status` enum('initiated','successful','failed','refunded') DEFAULT 'initiated',
  `paid_on` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `pharmacists` (
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `license_no` varchar(80) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `stock_requests` (
  `pharmacist_id` bigint(20) UNSIGNED NOT NULL,
  `company_id` bigint(20) UNSIGNED NOT NULL,
  `medicine_id` bigint(20) UNSIGNED DEFAULT NULL,
  `quantity` int(10) UNSIGNED DEFAULT NULL,
  `status` enum('pending','approved','rejected','fulfilled') DEFAULT 'pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `users` (
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `name` varchar(120) NOT NULL,
  `phone` bigint(20) UNSIGNED NOT NULL,
  `email` varchar(190) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `status` varchar(20) DEFAULT 'active',
  `role` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `wishlists` (
  `wishlist_id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `product_status` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



CREATE TABLE `wishlist_items` (
  `wishlist_id` bigint(20) UNSIGNED NOT NULL,
  `medicine_id` bigint(20) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `posts` (
  `post_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `title` varchar(255) NOT NULL,
  `content` text NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`post_id`),
  KEY `user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `notes` (
  `note_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `patient_id` bigint(20) UNSIGNED DEFAULT NULL,
  `content` text NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`note_id`),
  KEY `user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `notifications` (
  `notification_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `read_status` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`notification_id`),
  KEY `user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

ALTER TABLE `admins`
  ADD PRIMARY KEY (`user_id`);


ALTER TABLE `appointments`
  ADD PRIMARY KEY (`appointment_id`),
  ADD UNIQUE KEY `uk_appt_unique` (`doctor_id`,`scheduled_at`),
  ADD KEY `fk_appt_customer` (`customer_id`);


ALTER TABLE `carts`
  ADD PRIMARY KEY (`cart_id`),
  ADD KEY `fk_carts_customer` (`user_id`);


ALTER TABLE `cart_items`
  ADD PRIMARY KEY (`cart_id`,`medicine_id`),
  ADD KEY `fk_ci_medicine` (`medicine_id`);

-
ALTER TABLE `companies`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `uk_companies_license` (`license_no`);


ALTER TABLE `company_manufactures`
  ADD PRIMARY KEY (`company_id`,`medicine_id`),
  ADD KEY `fk_cm_medicine` (`medicine_id`);


ALTER TABLE `customer`
  ADD PRIMARY KEY (`user_id`);


ALTER TABLE `doctors`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `license_no` (`license_no`);


ALTER TABLE `feedbacks`
  ADD PRIMARY KEY (`feedback_id`),
  ADD UNIQUE KEY `uk_feedback_unique` (`customer_id`,`medicine_id`),
  ADD KEY `fk_feedback_medicine` (`medicine_id`);


ALTER TABLE `inventories`
  ADD PRIMARY KEY (`inventory_id`),
  ADD KEY `fk_inventories_company` (`company_id`),
  ADD KEY `fk_inventories_pharmacist` (`pharmacist_id`);

ALTER TABLE `inventory_items`
  ADD PRIMARY KEY (`inventory_id`,`medicine_id`),
  ADD KEY `fk_inventory_items_medicine` (`medicine_id`);

ALTER TABLE `medicines`
  ADD PRIMARY KEY (`medicine_id`);


ALTER TABLE `payments`
  ADD PRIMARY KEY (`order_id`),
  ADD KEY `fk_payment_cart` (`cart_id`),
  ADD KEY `fk_orders_customer` (`customer_id`);

ALTER TABLE `pharmacists`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `license_no` (`license_no`);

ALTER TABLE `stock_requests`
  ADD KEY `fk_sr_pharmacist` (`pharmacist_id`),
  ADD KEY `fk_sr_company` (`company_id`),
  ADD KEY `fk_sr_medicine` (`medicine_id`);

ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);

ALTER TABLE `wishlists`
  ADD PRIMARY KEY (`wishlist_id`),
  ADD KEY `fk_wishlists_user` (`user_id`);


ALTER TABLE `wishlist_items`
  ADD PRIMARY KEY (`wishlist_id`,`medicine_id`),
  ADD KEY `fk_wli_medicine` (`medicine_id`);


ALTER TABLE `admins`
  MODIFY `user_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;


ALTER TABLE `appointments`
  MODIFY `appointment_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;


ALTER TABLE `carts`
  MODIFY `cart_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;


ALTER TABLE `feedbacks`
  MODIFY `feedback_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;


ALTER TABLE `inventories`
  MODIFY `inventory_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `medicines`
  MODIFY `medicine_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `payments`
  MODIFY `order_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `users`
  MODIFY `user_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `wishlists`
  MODIFY `wishlist_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;


ALTER TABLE `admins`
  ADD CONSTRAINT `fk_admins_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `appointments`
  ADD CONSTRAINT `fk_appt_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_appt_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `carts`
  ADD CONSTRAINT `fk_carts_customer` FOREIGN KEY (`user_id`) REFERENCES `customer` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `cart_items`
  ADD CONSTRAINT `fk_ci_cart` FOREIGN KEY (`cart_id`) REFERENCES `carts` (`cart_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_ci_medicine` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `companies`
  ADD CONSTRAINT `fk_companies_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `company_manufactures`
  ADD CONSTRAINT `fk_cm_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_cm_medicine` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `customer`
  ADD CONSTRAINT `fk_customers_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `doctors`
  ADD CONSTRAINT `fk_doctors_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `feedbacks`
  ADD CONSTRAINT `fk_feedback_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_feedback_medicine` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `inventories`
  ADD CONSTRAINT `fk_inventories_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_inventories_pharmacist` FOREIGN KEY (`pharmacist_id`) REFERENCES `pharmacists` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `inventory_items`
  ADD CONSTRAINT `fk_inventory_items_inventory` FOREIGN KEY (`inventory_id`) REFERENCES `inventories` (`inventory_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_inventory_items_medicine` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON UPDATE CASCADE;

ALTER TABLE `payments`
  ADD CONSTRAINT `fk_orders_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_payment_cart` FOREIGN KEY (`cart_id`) REFERENCES `carts` (`cart_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `pharmacists`
  ADD CONSTRAINT `fk_pharmacists_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `stock_requests`
  ADD CONSTRAINT `fk_sr_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_sr_medicine` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_sr_pharmacist` FOREIGN KEY (`pharmacist_id`) REFERENCES `pharmacists` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `wishlists`
  ADD CONSTRAINT `fk_wishlists_user` FOREIGN KEY (`user_id`) REFERENCES `customer` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `wishlist_items`
  ADD CONSTRAINT `fk_wli_medicine` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_wli_wishlist` FOREIGN KEY (`wishlist_id`) REFERENCES `wishlists` (`wishlist_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

