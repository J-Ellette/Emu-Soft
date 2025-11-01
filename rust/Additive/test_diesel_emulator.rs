// Developed by PowerShield, as an alternative to Diesel

// Test suite for Diesel Emulator
// This file contains comprehensive tests for the Diesel ORM emulator

#[cfg(test)]
mod tests {
    // Import from the main diesel_emulator module
    include!("diesel_emulator.rs");

    #[test]
    fn test_postgres_connection() {
        let result = Connection::establish_postgres("postgres://localhost:5432/testdb");
        assert!(result.is_ok());
        let conn = result.unwrap();
        assert_eq!(conn.backend, "postgres");
    }

    #[test]
    fn test_mysql_connection() {
        let result = Connection::establish_mysql("mysql://root:password@localhost/testdb");
        assert!(result.is_ok());
        let conn = result.unwrap();
        assert_eq!(conn.backend, "mysql");
    }

    #[test]
    fn test_sqlite_connection() {
        let result = Connection::establish_sqlite(":memory:");
        assert!(result.is_ok());
        let conn = result.unwrap();
        assert_eq!(conn.backend, "sqlite");
    }

    #[test]
    fn test_execute_raw_sql() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();
        let result = conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)");
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 1);
    }

    #[test]
    fn test_transaction_commit() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();
        let transaction = conn.begin_transaction().unwrap();
        let result = transaction.commit();
        assert!(result.is_ok());
    }

    #[test]
    fn test_transaction_rollback() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();
        let transaction = conn.begin_transaction().unwrap();
        let result = transaction.rollback();
        assert!(result.is_ok());
    }

    #[test]
    fn test_row_operations() {
        let mut row = Row::new();
        row.set("name", Value::Text("Alice".to_string()));
        row.set("age", Value::Integer(30));

        assert!(row.get("name").is_some());
        assert!(row.get("age").is_some());
        assert!(row.get("email").is_none());

        if let Some(Value::Text(name)) = row.get("name") {
            assert_eq!(name, "Alice");
        } else {
            panic!("Expected text value");
        }
    }

    #[test]
    fn test_value_display() {
        assert_eq!(format!("{}", Value::Integer(42)), "42");
        assert_eq!(format!("{}", Value::BigInt(1000000)), "1000000");
        assert_eq!(format!("{}", Value::Text("hello".to_string())), "hello");
        assert_eq!(format!("{}", Value::Float(3.14)), "3.14");
        assert_eq!(format!("{}", Value::Boolean(true)), "true");
        assert_eq!(format!("{}", Value::Null), "NULL");
    }

    #[test]
    fn test_select_query_builder() {
        let query = SelectQuery::new("users")
            .select(vec!["id", "name", "email"])
            .filter("age > 18")
            .limit(10);

        let sql = query.to_sql();
        assert!(sql.contains("SELECT id, name, email FROM users"));
        assert!(sql.contains("WHERE age > 18"));
        assert!(sql.contains("LIMIT 10"));
    }

    #[test]
    fn test_select_with_order_by() {
        let query = SelectQuery::new("posts")
            .order_by("created_at", "DESC")
            .limit(5);

        let sql = query.to_sql();
        assert!(sql.contains("SELECT * FROM posts"));
        assert!(sql.contains("ORDER BY created_at DESC"));
        assert!(sql.contains("LIMIT 5"));
    }

    #[test]
    fn test_select_with_offset() {
        let query = SelectQuery::new("products")
            .limit(20)
            .offset(40);

        let sql = query.to_sql();
        assert!(sql.contains("LIMIT 20"));
        assert!(sql.contains("OFFSET 40"));
    }

    #[test]
    fn test_insert_query_builder() {
        let query = InsertQuery::new("users")
            .value("name", Value::Text("Bob".to_string()))
            .value("age", Value::Integer(25))
            .value("email", Value::Text("bob@example.com".to_string()));

        let sql = query.to_sql();
        assert!(sql.contains("INSERT INTO users"));
        assert!(sql.contains("name"));
        assert!(sql.contains("age"));
        assert!(sql.contains("email"));
    }

    #[test]
    fn test_insert_execution() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();
        let result = InsertQuery::new("users")
            .value("name", Value::Text("Charlie".to_string()))
            .value("age", Value::Integer(28))
            .execute(&conn);

        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 1);
    }

    #[test]
    fn test_update_query_builder() {
        let query = UpdateQuery::new("users")
            .set("name", Value::Text("Updated Name".to_string()))
            .set("age", Value::Integer(35))
            .filter("id = 1");

        let sql = query.to_sql();
        assert!(sql.contains("UPDATE users SET"));
        assert!(sql.contains("name = Updated Name"));
        assert!(sql.contains("age = 35"));
        assert!(sql.contains("WHERE id = 1"));
    }

    #[test]
    fn test_update_execution() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();
        let result = UpdateQuery::new("users")
            .set("status", Value::Text("active".to_string()))
            .filter("age > 18")
            .execute(&conn);

        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 1);
    }

    #[test]
    fn test_delete_query_builder() {
        let query = DeleteQuery::new("users").filter("inactive = true");

        let sql = query.to_sql();
        assert!(sql.contains("DELETE FROM users"));
        assert!(sql.contains("WHERE inactive = true"));
    }

    #[test]
    fn test_delete_without_filter() {
        let query = DeleteQuery::new("temp_data");

        let sql = query.to_sql();
        assert_eq!(sql, "DELETE FROM temp_data");
    }

    #[test]
    fn test_delete_execution() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();

        // Insert some data first
        InsertQuery::new("users")
            .value("name", Value::Text("Test".to_string()))
            .execute(&conn)
            .unwrap();

        // Delete it
        let result = DeleteQuery::new("users")
            .filter("name = 'Test'")
            .execute(&conn);

        assert!(result.is_ok());
    }

    #[test]
    fn test_migration_create_table() {
        let migration = Migration::new().create_table(
            "posts",
            vec![
                ("id", "INTEGER PRIMARY KEY"),
                ("title", "TEXT NOT NULL"),
                ("content", "TEXT"),
                ("created_at", "TIMESTAMP"),
            ],
        );

        assert_eq!(migration.operations.len(), 1);
        assert!(migration.operations[0].contains("CREATE TABLE posts"));
    }

    #[test]
    fn test_migration_drop_table() {
        let migration = Migration::new().drop_table("old_table");

        assert_eq!(migration.operations.len(), 1);
        assert!(migration.operations[0].contains("DROP TABLE old_table"));
    }

    #[test]
    fn test_migration_add_column() {
        let migration = Migration::new().add_column("users", "phone", "VARCHAR(20)");

        assert_eq!(migration.operations.len(), 1);
        assert!(migration.operations[0].contains("ALTER TABLE users"));
        assert!(migration.operations[0].contains("ADD COLUMN phone VARCHAR(20)"));
    }

    #[test]
    fn test_migration_remove_column() {
        let migration = Migration::new().remove_column("users", "deprecated_field");

        assert_eq!(migration.operations.len(), 1);
        assert!(migration.operations[0].contains("ALTER TABLE users"));
        assert!(migration.operations[0].contains("DROP COLUMN deprecated_field"));
    }

    #[test]
    fn test_migration_multiple_operations() {
        let migration = Migration::new()
            .create_table("categories", vec![("id", "INTEGER"), ("name", "TEXT")])
            .add_column("products", "category_id", "INTEGER")
            .drop_table("legacy_table");

        assert_eq!(migration.operations.len(), 3);
    }

    #[test]
    fn test_migration_run() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();
        let migration = Migration::new()
            .create_table("test", vec![("id", "INTEGER")])
            .add_column("test", "name", "TEXT");

        let result = migration.run(&conn);
        assert!(result.is_ok());
    }

    #[test]
    fn test_table_dsl() {
        let users = Table::new("users");
        assert_eq!(users.name, "users");
    }

    #[test]
    fn test_table_select() {
        let users = Table::new("users");
        let query = users.select().filter("age > 21").limit(5);

        let sql = query.to_sql();
        assert!(sql.contains("SELECT * FROM users"));
        assert!(sql.contains("WHERE age > 21"));
        assert!(sql.contains("LIMIT 5"));
    }

    #[test]
    fn test_table_insert() {
        let users = Table::new("users");
        let query = users
            .insert()
            .value("name", Value::Text("Dave".to_string()));

        let sql = query.to_sql();
        assert!(sql.contains("INSERT INTO users"));
    }

    #[test]
    fn test_table_update() {
        let users = Table::new("users");
        let query = users
            .update()
            .set("status", Value::Text("verified".to_string()))
            .filter("email_verified = true");

        let sql = query.to_sql();
        assert!(sql.contains("UPDATE users SET"));
    }

    #[test]
    fn test_table_delete() {
        let users = Table::new("users");
        let query = users.delete().filter("last_login < '2020-01-01'");

        let sql = query.to_sql();
        assert!(sql.contains("DELETE FROM users"));
    }

    #[test]
    fn test_table_count() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();
        let users = Table::new("users");

        // Initial count should be 0
        let count = users.count(&conn);
        assert!(count.is_ok());
        assert_eq!(count.unwrap(), 0);

        // Insert and count again
        users
            .insert()
            .value("name", Value::Text("Test".to_string()))
            .execute(&conn)
            .unwrap();

        let count = users.count(&conn);
        assert!(count.is_ok());
        assert_eq!(count.unwrap(), 1);
    }

    #[test]
    fn test_full_crud_cycle() {
        let conn = Connection::establish_sqlite(":memory:").unwrap();
        let users = Table::new("users");

        // Create
        let insert_result = users
            .insert()
            .value("name", Value::Text("Eva".to_string()))
            .value("age", Value::Integer(27))
            .execute(&conn);
        assert!(insert_result.is_ok());

        // Read
        let select_result = users.select().load(&conn);
        assert!(select_result.is_ok());

        // Update
        let update_result = users
            .update()
            .set("age", Value::Integer(28))
            .filter("name = 'Eva'")
            .execute(&conn);
        assert!(update_result.is_ok());

        // Delete
        let delete_result = users.delete().filter("name = 'Eva'").execute(&conn);
        assert!(delete_result.is_ok());
    }

    #[test]
    fn test_complex_query_chain() {
        let query = SelectQuery::new("products")
            .select(vec!["id", "name", "price", "stock"])
            .filter("category = 'electronics' AND stock > 0")
            .order_by("price", "DESC")
            .limit(25)
            .offset(0);

        let sql = query.to_sql();
        assert!(sql.contains("SELECT id, name, price, stock FROM products"));
        assert!(sql.contains("WHERE category = 'electronics' AND stock > 0"));
        assert!(sql.contains("ORDER BY price DESC"));
        assert!(sql.contains("LIMIT 25"));
        assert!(sql.contains("OFFSET 0"));
    }
}

fn main() {
    println!("Running Diesel Emulator tests...");
    println!("Use 'cargo test' to run all tests");
}
