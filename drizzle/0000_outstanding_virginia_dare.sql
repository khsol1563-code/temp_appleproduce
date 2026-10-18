CREATE TABLE `submissions` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`student_name` text NOT NULL,
	`solution` text NOT NULL,
	`reason` text NOT NULL,
	`observation` text DEFAULT '' NOT NULL,
	`teacher_feedback` text DEFAULT '' NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
