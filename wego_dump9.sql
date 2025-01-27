-- MySQL dump 10.13  Distrib 8.0.36, for Win64 (x86_64)
--
-- Host: localhost    Database: wego_db
-- ------------------------------------------------------
-- Server version	8.0.36

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admins` (
  `username` varchar(128) NOT NULL,
  `first_name` varchar(128) NOT NULL,
  `last_name` varchar(128) NOT NULL,
  `email` varchar(250) NOT NULL,
  `phone_number` int NOT NULL,
  `password_hash` varchar(250) NOT NULL,
  `session_id` varchar(250) DEFAULT NULL,
  `reset_token` varchar(250) DEFAULT NULL,
  `admin_level` enum('superadmin','moderator') DEFAULT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `blocked` tinyint(1) DEFAULT '0',
  `deleted` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `phone_number` (`phone_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admins`
--

LOCK TABLES `admins` WRITE;
/*!40000 ALTER TABLE `admins` DISABLE KEYS */;
INSERT INTO `admins` VALUES ('Andinet','Andinet','Endale','andinetendale@gmail.com',22321,'$2b$12$eCZd/DJUTTho7qSpmmQOz.uj1DLFJE1Nkxc9jRasnkeNTuUaGUCDy',NULL,NULL,'superadmin','71782a92-f7d3-4ba4-9020-bf16f0a73509','2024-10-24 07:35:58','2024-10-24 07:37:32',0,0),('Bereket','Bereket','Zeselassie','bereketzeselassie@gmail.com',41353944,'$2b$12$GiAazVP05GVNj1Z6Cr.6lukSt6Bj5xadWLabXpskmxXSLM2K56pcS',NULL,NULL,'moderator','7409b50a-72c7-485e-95e9-28895b94a005','2024-10-15 19:48:33','2024-10-24 08:11:06',0,0),('daniel','daniel','bini','bereketzeselsie@gmail.com',2312,'$2b$12$u2ycjoNouF1qc0huP4pIqefum7hAzn5qzXd6ooVmo2CKMpvjI5YEm',NULL,NULL,'moderator','fc22255a-ac3c-4ca1-b751-c9afea537617','2024-10-24 08:20:42','2024-10-24 08:20:42',0,0);
/*!40000 ALTER TABLE `admins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `availabilities`
--

DROP TABLE IF EXISTS `availabilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `availabilities` (
  `driver_id` varchar(128) DEFAULT NULL,
  `location_id` varchar(128) DEFAULT NULL,
  `is_available` tinyint(1) DEFAULT NULL,
  `last_active_time` datetime DEFAULT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `driver_id` (`driver_id`),
  KEY `location_id` (`location_id`),
  CONSTRAINT `availabilities_ibfk_1` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`),
  CONSTRAINT `availabilities_ibfk_2` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `availabilities`
--

LOCK TABLES `availabilities` WRITE;
/*!40000 ALTER TABLE `availabilities` DISABLE KEYS */;
INSERT INTO `availabilities` VALUES ('60d33c0a-8b05-4665-a5e9-6ac2455eab3e',NULL,1,'2024-10-28 20:19:52','009d0c1a-b520-4560-84dc-b95c31eadac7','2024-10-15 14:13:08','2024-10-15 14:13:08'),('85f1c9be-aba8-4b80-8613-4925c1964eb4',NULL,1,NULL,'95d478fa-7ea5-44f3-8f51-d6cdf21f8b69','2024-10-15 14:14:02','2024-10-15 14:14:02'),('8f0302cb-0e0e-4ad6-b2f6-839f71fccde0',NULL,0,NULL,'ba84c186-9656-4ab9-b0d5-3f0290952580','2024-10-15 14:13:39','2024-10-15 14:13:39'),('dad730e7-d777-4e95-9774-1d205dc533c0',NULL,1,'2024-10-23 15:53:48','f267e736-8dd4-4c7c-9127-5c37cc4e6926','2024-10-15 14:14:14','2024-10-15 14:14:14');
/*!40000 ALTER TABLE `availabilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `drivers`
--

DROP TABLE IF EXISTS `drivers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `drivers` (
  `username` varchar(128) NOT NULL,
  `first_name` varchar(128) NOT NULL,
  `last_name` varchar(128) NOT NULL,
  `email` varchar(250) NOT NULL,
  `phone_number` int NOT NULL,
  `password_hash` varchar(250) NOT NULL,
  `reset_token` varchar(250) DEFAULT NULL,
  `payment_method` varchar(128) NOT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT '0',
  `blocked` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `phone_number` (`phone_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `drivers`
--

LOCK TABLES `drivers` WRITE;
/*!40000 ALTER TABLE `drivers` DISABLE KEYS */;
INSERT INTO `drivers` VALUES ('jackie','jack','john','jackjohn@gmail.com',588111,'$2b$12$OiTIGCJtgUOFPnum2DAfieUyRzT6q2Y0qWkeM94CdvTNuHYn/0J5y',NULL,'Cash','60d33c0a-8b05-4665-a5e9-6ac2455eab3e','2024-10-15 13:54:59','2024-10-17 14:25:52',0,0),('bk','bereket','zese','bkzese@gmail.com',78494,'$2b$12$3ZzRJJK0JSuXGDsMV.QYxOu9li9wpdQX1XujNeONSkZD4GzhZG2Me',NULL,'Cash','85f1c9be-aba8-4b80-8613-4925c1964eb4','2024-10-15 13:55:51','2024-10-15 13:55:51',0,0),('dani','daniel','belay','danielbelay@gmail.com',919111,'$2b$12$mCjPn/2XMNrlmVR75GKzKOpHIXFbkHbrLhNo2pzGnUHwNlEOOmhDC',NULL,'TeleBirr','8f0302cb-0e0e-4ad6-b2f6-839f71fccde0','2024-10-15 13:57:18','2024-10-15 13:57:18',0,0),('abrsh','abrha','hagos','abrhahagos@gmail.com',8787,'$2b$12$PCjNX9hzj0ZS7M/TlnAgzOmRk4F7LBvysVoAbRJ73aEBvfd74BP1S',NULL,'TeleBirr','dad730e7-d777-4e95-9774-1d205dc533c0','2024-10-15 13:56:31','2024-10-20 12:20:10',0,0);
/*!40000 ALTER TABLE `drivers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `locations` (
  `latitude` float DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  `address` varchar(128) DEFAULT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
/*!40000 ALTER TABLE `locations` DISABLE KEYS */;
INSERT INTO `locations` VALUES (131231,214122,'Oromo','2b4f2cd0-d4dd-478e-b483-adb1baac7b3c','2024-10-28 20:41:22','2024-10-28 20:41:22'),(2131,13213,'Bole','34d0d25b-a9c0-43a3-90b3-d75823e09371','2024-10-16 07:32:42','2024-10-16 07:32:42'),(1233,21313,'Ambo','67348cb8-52b8-4fd8-816b-be276fa84154','2024-10-16 07:58:34','2024-10-16 07:58:34'),(1233,21313,'Welo','72ce52e6-b883-4f0b-a743-f5a26fa43461','2024-10-16 07:58:40','2024-10-16 07:58:40'),(2131,13213,'Adama','de349a88-a153-43ca-b3bf-efab0e90fad2','2024-10-16 07:32:49','2024-10-16 07:32:49');
/*!40000 ALTER TABLE `locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `driver_id` varchar(128) DEFAULT NULL,
  `rider_id` varchar(128) DEFAULT NULL,
  `message` varchar(1024) DEFAULT NULL,
  `notification_type` varchar(128) DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT NULL,
  `read_at` datetime DEFAULT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `driver_id` (`driver_id`),
  KEY `rider_id` (`rider_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`),
  CONSTRAINT `notifications_ibfk_2` FOREIGN KEY (`rider_id`) REFERENCES `riders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `trip_id` varchar(128) DEFAULT NULL,
  `payment_method` varchar(128) NOT NULL,
  `payment_time` datetime NOT NULL,
  `amount` float NOT NULL,
  `payment_status` varchar(128) NOT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `rider_id` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trip_id` (`trip_id`),
  KEY `payment` (`rider_id`),
  CONSTRAINT `payment` FOREIGN KEY (`rider_id`) REFERENCES `riders` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`trip_id`) REFERENCES `trips` (`id`),
  CONSTRAINT `rider_id` FOREIGN KEY (`rider_id`) REFERENCES `riders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
INSERT INTO `payments` VALUES ('05d5dfae-3a44-4f5c-b827-be00c09603a2','Cash','2024-10-28 06:49:41',123.2,'paid','88e70521-9b8c-4bc3-9664-ef1adbbbc76d','2024-10-28 06:49:41','2024-10-28 06:49:41','6d66c6fb-8dcc-48d9-b71e-81b7dc7693cf'),('05d5dfae-3a44-4f5c-b827-be00c09603a2','Cash','2024-10-28 06:50:46',123.2,'paid','bc933f60-83a4-46e1-8e69-3c9679d0ea6b','2024-10-28 06:50:46','2024-10-28 06:50:46','da95d66e-62ed-41c6-9e85-c4f4cb7e06f6');
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `riders`
--

DROP TABLE IF EXISTS `riders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `riders` (
  `username` varchar(128) NOT NULL,
  `first_name` varchar(128) NOT NULL,
  `last_name` varchar(128) NOT NULL,
  `email` varchar(250) NOT NULL,
  `phone_number` int NOT NULL,
  `password_hash` varchar(250) NOT NULL,
  `reset_token` varchar(250) DEFAULT NULL,
  `payment_method` varchar(128) NOT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `blocked` tinyint(1) DEFAULT '0',
  `deleted` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `phone_number` (`phone_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `riders`
--

LOCK TABLES `riders` WRITE;
/*!40000 ALTER TABLE `riders` DISABLE KEYS */;
INSERT INTO `riders` VALUES ('sams','samson','halu','somsonhailu@gmail.com',55,'$2b$12$/WM7Oxe7hwavKQ4Teo3.Neh4lgtxTCpuAdx5zjh9H9uF2EHGo46Du',NULL,'TeleBirr','0e5dec68-f978-4c89-a32c-4478bed8efb0','2024-10-17 11:36:02','2024-10-17 11:36:02',1,0),('melat','melat','asefa','melatasefa@gmail.com',1977,'$2b$12$YmyJTdTVVOtnrojG4snY3.GCPaN5pWKieN0WEUWJ34unwFhpdixM2',NULL,'Cash','27f11cff-6b5a-43c4-a053-a0cc0251ddca','2024-10-15 14:02:19','2024-10-15 14:02:19',0,1),('hailu','hailu','sami','hailusami@gmail.com',19194,'$2b$12$lvzoFbpVjZvJfd8Si.QFleRNA7z5M34uC3cKHJIhn3oRfOJQVHccy',NULL,'Cash','3e8889cd-726f-42df-a213-00d261c63153','2024-10-15 14:00:44','2024-10-15 14:00:44',0,0),('nati','natinaiel','kflom','natinaielkflom@gmail.com',9918,'$2b$12$1//o8LDbxzpJoWoMBwmdeeF4AryaYSeBW.zZTuTa.8XAwj4ttNPaC',NULL,'Cash','6d66c6fb-8dcc-48d9-b71e-81b7dc7693cf','2024-10-15 14:01:32','2024-10-15 14:01:32',0,0),('kb','kbrom','abera','kbromabera@gmail.com',6618,'$2b$12$gtzBrqKeWy/Bsz6vHWbr7.8.aryqZ1ZBzVAvQ64Hr0AP9tkUTH/Oq',NULL,'TeleBirr','7f8f44f2-6162-4086-a624-a8cce59e579a','2024-10-15 13:59:58','2024-10-15 13:59:58',0,0),('hana','hana','john','hanajohn@gmail.com',1112,'$2b$12$/6pGNfrabmNVnNGfzDACEOhhm4BLSzJhdJNEMgMksKb15TOsJG1mS',NULL,'Cash','9630aa77-1448-4131-b4ff-764df4061db4','2024-10-29 14:24:43','2024-10-29 14:24:43',0,0),('sami','samiel','daniel','samieldaniel@gmail.com',7881,'$2b$12$7M8oYFTo1kW.LmOVzmcc.OtiJKgNJ2Cmub2hS6spzSV/tB8oSB3pS',NULL,'TeleBirr','da95d66e-62ed-41c6-9e85-c4f4cb7e06f6','2024-10-15 13:59:28','2024-10-15 13:59:28',0,0);
/*!40000 ALTER TABLE `riders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trip_riders`
--

DROP TABLE IF EXISTS `trip_riders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trip_riders` (
  `trip_id` varchar(128) NOT NULL,
  `rider_id` varchar(128) NOT NULL,
  `is_past` tinyint(1) DEFAULT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `status` varchar(128) DEFAULT 'booked',
  `status_by` varchar(128) DEFAULT 'rider',
  PRIMARY KEY (`trip_id`,`rider_id`,`id`),
  KEY `rider_id` (`rider_id`),
  CONSTRAINT `trip_riders_ibfk_1` FOREIGN KEY (`trip_id`) REFERENCES `trips` (`id`),
  CONSTRAINT `trip_riders_ibfk_2` FOREIGN KEY (`rider_id`) REFERENCES `riders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trip_riders`
--

LOCK TABLES `trip_riders` WRITE;
/*!40000 ALTER TABLE `trip_riders` DISABLE KEYS */;
INSERT INTO `trip_riders` VALUES ('05d5dfae-3a44-4f5c-b827-be00c09603a2','6d66c6fb-8dcc-48d9-b71e-81b7dc7693cf',0,'2c14d9a3-1c7d-4420-9c12-219d60406d9b','2024-10-28 06:20:18','2024-10-28 06:20:18','booked','rider'),('05d5dfae-3a44-4f5c-b827-be00c09603a2','7f8f44f2-6162-4086-a624-a8cce59e579a',0,'b825bfdb-183b-4987-b349-2783c2a01126','2024-10-28 12:09:46','2024-10-28 12:09:46','booked','rider'),('05d5dfae-3a44-4f5c-b827-be00c09603a2','da95d66e-62ed-41c6-9e85-c4f4cb7e06f6',1,'86d10a97-10bf-42f3-881c-35d0011787cf','2024-10-28 06:21:47','2024-10-28 06:21:47','Canceled','rider'),('0c5c4a4e-5611-4645-a124-ee90a0273a6e','6d66c6fb-8dcc-48d9-b71e-81b7dc7693cf',0,'c20e81cc-2ed3-4492-b8e4-ba44510542eb','2024-10-28 06:20:11','2024-10-28 06:20:11','booked','rider');
/*!40000 ALTER TABLE `trip_riders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trips`
--

DROP TABLE IF EXISTS `trips`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trips` (
  `driver_id` varchar(128) DEFAULT NULL,
  `pickup_location_id` varchar(128) DEFAULT NULL,
  `dropoff_location_id` varchar(128) DEFAULT NULL,
  `pickup_time` datetime DEFAULT NULL,
  `dropoff_time` datetime DEFAULT NULL,
  `fare` float NOT NULL,
  `distance` float DEFAULT NULL,
  `status` varchar(128) NOT NULL,
  `is_available` tinyint(1) DEFAULT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `driver_id` (`driver_id`),
  KEY `pickup_location_id` (`pickup_location_id`),
  KEY `dropoff_location_id` (`dropoff_location_id`),
  CONSTRAINT `trips_ibfk_1` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`),
  CONSTRAINT `trips_ibfk_2` FOREIGN KEY (`pickup_location_id`) REFERENCES `locations` (`id`),
  CONSTRAINT `trips_ibfk_3` FOREIGN KEY (`dropoff_location_id`) REFERENCES `locations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trips`
--

LOCK TABLES `trips` WRITE;
/*!40000 ALTER TABLE `trips` DISABLE KEYS */;
INSERT INTO `trips` VALUES ('dad730e7-d777-4e95-9774-1d205dc533c0','34d0d25b-a9c0-43a3-90b3-d75823e09371','de349a88-a153-43ca-b3bf-efab0e90fad2',NULL,NULL,123.2,132.2,'Canceled',1,'05d5dfae-3a44-4f5c-b827-be00c09603a2','2024-10-16 07:35:23','2024-10-17 14:00:11'),('8f0302cb-0e0e-4ad6-b2f6-839f71fccde0','72ce52e6-b883-4f0b-a743-f5a26fa43461','67348cb8-52b8-4fd8-816b-be276fa84154',NULL,NULL,123.2,1321.2,'Canceled',1,'07c5334d-ed07-4896-b43f-c498db3399d5','2024-10-16 08:00:48','2024-10-16 08:00:48'),('dad730e7-d777-4e95-9774-1d205dc533c0','34d0d25b-a9c0-43a3-90b3-d75823e09371','67348cb8-52b8-4fd8-816b-be276fa84154',NULL,NULL,21.2,213.2,'in-Progress',1,'0c5c4a4e-5611-4645-a124-ee90a0273a6e','2024-10-17 11:27:22','2024-10-17 11:27:22'),('60d33c0a-8b05-4665-a5e9-6ac2455eab3e','2b4f2cd0-d4dd-478e-b483-adb1baac7b3c','34d0d25b-a9c0-43a3-90b3-d75823e09371','2024-10-28 00:00:00','2024-10-28 00:00:00',150,203,'available',1,'3ef36580-2426-454f-b879-46c10c861e32','2024-10-28 20:52:25','2024-10-28 20:52:25'),('dad730e7-d777-4e95-9774-1d205dc533c0','34d0d25b-a9c0-43a3-90b3-d75823e09371','67348cb8-52b8-4fd8-816b-be276fa84154',NULL,NULL,21.2,213.2,'Reqested',1,'6749d803-671a-4048-a440-a91f65dcd09b','2024-10-17 11:27:08','2024-10-17 11:27:08'),('85f1c9be-aba8-4b80-8613-4925c1964eb4','72ce52e6-b883-4f0b-a743-f5a26fa43461','de349a88-a153-43ca-b3bf-efab0e90fad2',NULL,NULL,21.2,213.2,'in-Progress',1,'7c4b0ad1-fd30-46b7-b869-fed673b6b071','2024-10-17 11:28:12','2024-10-17 11:28:12'),('60d33c0a-8b05-4665-a5e9-6ac2455eab3e','34d0d25b-a9c0-43a3-90b3-d75823e09371','67348cb8-52b8-4fd8-816b-be276fa84154',NULL,NULL,213.2,123,'requested',1,'a1dea010-6f6b-47b8-b09c-ce90310c2510','2024-10-20 08:45:41','2024-10-20 08:45:41'),('8f0302cb-0e0e-4ad6-b2f6-839f71fccde0','72ce52e6-b883-4f0b-a743-f5a26fa43461','de349a88-a153-43ca-b3bf-efab0e90fad2',NULL,NULL,21.2,213.2,'in-Progress',1,'e780dc4f-d08b-47ca-abfa-e0b318163a43','2024-10-17 11:27:56','2024-10-17 11:27:56');
/*!40000 ALTER TABLE `trips` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vehicles`
--

DROP TABLE IF EXISTS `vehicles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vehicles` (
  `driver_id` varchar(128) DEFAULT NULL,
  `type` varchar(60) DEFAULT NULL,
  `model` varchar(60) DEFAULT NULL,
  `color` varchar(60) NOT NULL,
  `seating_capacity` int NOT NULL,
  `id` varchar(60) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `driver_id` (`driver_id`),
  CONSTRAINT `vehicles_ibfk_1` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicles`
--

LOCK TABLES `vehicles` WRITE;
/*!40000 ALTER TABLE `vehicles` DISABLE KEYS */;
INSERT INTO `vehicles` VALUES ('60d33c0a-8b05-4665-a5e9-6ac2455eab3e','Corolla',NULL,'White',3,'301aac56-ca95-4afd-8f81-b5583cea23e2','2024-10-15 14:05:55','2024-10-15 14:05:55'),('8f0302cb-0e0e-4ad6-b2f6-839f71fccde0','nisan',NULL,'Black',4,'772cdad2-3065-4474-bf7d-cc244f6a18dc','2024-10-15 14:05:07','2024-10-15 14:05:07'),('85f1c9be-aba8-4b80-8613-4925c1964eb4','Corolla',NULL,'White',3,'a3d86838-1032-4176-ab5e-e8f77a38f2a3','2024-10-15 14:05:42','2024-10-15 14:05:42'),('dad730e7-d777-4e95-9774-1d205dc533c0','Vitz',NULL,'Red',3,'d57c3f29-521f-4f6e-96f7-353fede215d4','2024-10-15 14:04:11','2024-10-15 14:04:11');
/*!40000 ALTER TABLE `vehicles` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-10-30 19:47:54
