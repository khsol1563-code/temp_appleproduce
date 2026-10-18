import { sql } from "drizzle-orm";
import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";
export const submissions = sqliteTable("submissions", {id:integer("id").primaryKey({autoIncrement:true}),studentName:text("student_name").notNull(),solution:text("solution").notNull(),reason:text("reason").notNull(),observation:text("observation").notNull().default(""),teacherFeedback:text("teacher_feedback").notNull().default(""),createdAt:text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`)});
