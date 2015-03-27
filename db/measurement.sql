CREATE TABLE `measurement` (
  `id` bigint(11) unsigned NOT NULL AUTO_INCREMENT,
  `hostname` varchar(100) NOT NULL DEFAULT '',
  `measurement_type` smallint(6) NOT NULL,
  `destination_list` text NOT NULL,
  `current_destination` varchar(39) DEFAULT NULL,
  `measurement_start_time` bigint(20) DEFAULT NULL,
  `finished` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `hostname` (`hostname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
