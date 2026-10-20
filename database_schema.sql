-- MySQL dump 10.13  Distrib 8.0.26, for Win64 (x86_64)
--
-- Host: localhost    Database: data_quality_platform
-- ------------------------------------------------------
-- Server version	8.0.26

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alerts`
--

DROP TABLE IF EXISTS `alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alerts` (
  `alert_id` int NOT NULL AUTO_INCREMENT,
  `run_id` int NOT NULL,
  `dataset_id` int NOT NULL,
  `alert_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `severity` enum('INFO','WARNING','CRITICAL') COLLATE utf8mb4_unicode_ci DEFAULT 'WARNING',
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_resolved` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`alert_id`),
  KEY `run_id` (`run_id`),
  KEY `dataset_id` (`dataset_id`),
  CONSTRAINT `alerts_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `pipeline_runs` (`run_id`),
  CONSTRAINT `alerts_ibfk_2` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`dataset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `data_sources`
--

DROP TABLE IF EXISTS `data_sources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `data_sources` (
  `source_id` int NOT NULL AUTO_INCREMENT,
  `source_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_type` enum('CSV','MYSQL') COLLATE utf8mb4_unicode_ci NOT NULL,
  `connection_config` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`source_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dataset_metrics`
--

DROP TABLE IF EXISTS `dataset_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataset_metrics` (
  `metric_id` int NOT NULL AUTO_INCREMENT,
  `run_id` int NOT NULL,
  `dataset_id` int NOT NULL,
  `row_count` bigint DEFAULT '0',
  `column_count` int DEFAULT '0',
  `schema_snapshot` json DEFAULT NULL,
  `null_count` bigint DEFAULT '0',
  `duplicate_count` bigint DEFAULT '0',
  `recorded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`metric_id`),
  KEY `run_id` (`run_id`),
  KEY `dataset_id` (`dataset_id`),
  CONSTRAINT `dataset_metrics_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `pipeline_runs` (`run_id`),
  CONSTRAINT `dataset_metrics_ibfk_2` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`dataset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `datasets`
--

DROP TABLE IF EXISTS `datasets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `datasets` (
  `dataset_id` int NOT NULL AUTO_INCREMENT,
  `source_id` int NOT NULL,
  `dataset_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `table_name` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`dataset_id`),
  KEY `source_id` (`source_id`),
  CONSTRAINT `datasets_ibfk_1` FOREIGN KEY (`source_id`) REFERENCES `data_sources` (`source_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pipeline_runs`
--

DROP TABLE IF EXISTS `pipeline_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pipeline_runs` (
  `run_id` int NOT NULL AUTO_INCREMENT,
  `dataset_id` int NOT NULL,
  `started_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `finished_at` timestamp NULL DEFAULT NULL,
  `status` enum('RUNNING','SUCCESS','FAILED') COLLATE utf8mb4_unicode_ci DEFAULT 'RUNNING',
  `total_rows` bigint DEFAULT '0',
  `quality_score` decimal(5,2) DEFAULT NULL,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`run_id`),
  KEY `dataset_id` (`dataset_id`),
  CONSTRAINT `pipeline_runs_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`dataset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `quality_results`
--

DROP TABLE IF EXISTS `quality_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quality_results` (
  `result_id` int NOT NULL AUTO_INCREMENT,
  `run_id` int NOT NULL,
  `rule_id` int NOT NULL,
  `checked_rows` bigint DEFAULT '0',
  `failed_rows` bigint DEFAULT '0',
  `pass_rate` decimal(5,2) DEFAULT NULL,
  `result_status` enum('PASS','FAIL') COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`result_id`),
  KEY `run_id` (`run_id`),
  KEY `rule_id` (`rule_id`),
  CONSTRAINT `quality_results_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `pipeline_runs` (`run_id`),
  CONSTRAINT `quality_results_ibfk_2` FOREIGN KEY (`rule_id`) REFERENCES `quality_rules` (`rule_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `quality_rules`
--

DROP TABLE IF EXISTS `quality_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quality_rules` (
  `rule_id` int NOT NULL AUTO_INCREMENT,
  `dataset_id` int NOT NULL,
  `column_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rule_type` enum('NOT_NULL','UNIQUE','BETWEEN','MIN_VALUE','MAX_VALUE','ALLOWED_VALUES','REGEX') COLLATE utf8mb4_unicode_ci NOT NULL,
  `rule_config` json DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`rule_id`),
  KEY `dataset_id` (`dataset_id`),
  CONSTRAINT `quality_rules_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`dataset_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-20  7:36:45
