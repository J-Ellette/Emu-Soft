package main

// Developed by PowerShield, as an alternative to GORM
import (
	"errors"
	"fmt"
	"reflect"
	"strings"
	"time"
)

// DB represents a GORM database connection
type DB struct {
	records   map[string][]map[string]interface{}
	chain     *DB
	tableName string
	where     []whereClause
	limit     int
	offset    int
	order     string
	Error     error
	RowsAffected int64
}

type whereClause struct {
	condition string
	args      []interface{}
}

// Model represents a database model with common fields
type Model struct {
	ID        uint      `gorm:"primaryKey"`
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt *time.Time `gorm:"index"`
}

// Open creates a new database connection
func Open(dialect string, connectionString string) (*DB, error) {
	if dialect == "" || connectionString == "" {
		return nil, errors.New("invalid connection parameters")
	}
	
	return &DB{
		records: make(map[string][]map[string]interface{}),
		limit:   -1,
		offset:  0,
	}, nil
}

// Table specifies the table to operate on
func (db *DB) Table(name string) *DB {
	newDB := db.clone()
	newDB.tableName = name
	return newDB
}

// Model specifies the model to operate on
func (db *DB) Model(value interface{}) *DB {
	newDB := db.clone()
	newDB.tableName = getTableName(value)
	return newDB
}

// Where adds a WHERE clause
func (db *DB) Where(condition string, args ...interface{}) *DB {
	newDB := db.clone()
	newDB.where = append(newDB.where, whereClause{
		condition: condition,
		args:      args,
	})
	return newDB
}

// First finds the first record
func (db *DB) First(dest interface{}) *DB {
	newDB := db.clone()
	tableName := db.tableName
	if tableName == "" {
		tableName = getTableName(dest)
	}
	
	records, exists := db.records[tableName]
	if !exists || len(records) == 0 {
		newDB.Error = errors.New("record not found")
		return newDB
	}
	
	filtered := db.applyFilters(records)
	if len(filtered) == 0 {
		newDB.Error = errors.New("record not found")
		return newDB
	}
	
	mapToStruct(filtered[0], dest)
	newDB.RowsAffected = 1
	return newDB
}

// Find finds records that match given conditions
func (db *DB) Find(dest interface{}) *DB {
	newDB := db.clone()
	tableName := db.tableName
	if tableName == "" {
		tableName = getTableName(dest)
	}
	
	records, exists := db.records[tableName]
	if !exists {
		newDB.RowsAffected = 0
		return newDB
	}
	
	filtered := db.applyFilters(records)
	
	destValue := reflect.ValueOf(dest)
	if destValue.Kind() != reflect.Ptr {
		newDB.Error = errors.New("destination must be a pointer")
		return newDB
	}
	
	destValue = destValue.Elem()
	if destValue.Kind() == reflect.Slice {
		for _, record := range filtered {
			elemType := destValue.Type().Elem()
			newElem := reflect.New(elemType).Interface()
			mapToStruct(record, newElem)
			destValue.Set(reflect.Append(destValue, reflect.ValueOf(newElem).Elem()))
		}
	} else {
		if len(filtered) > 0 {
			mapToStruct(filtered[0], dest)
		}
	}
	
	newDB.RowsAffected = int64(len(filtered))
	return newDB
}

// Create inserts a new record
func (db *DB) Create(value interface{}) *DB {
	newDB := db.clone()
	tableName := db.tableName
	if tableName == "" {
		tableName = getTableName(value)
	}
	
	record := structToMap(value)
	
	// Set timestamps if they exist
	if _, ok := record["CreatedAt"]; ok {
		record["CreatedAt"] = time.Now()
	}
	if _, ok := record["UpdatedAt"]; ok {
		record["UpdatedAt"] = time.Now()
	}
	
	// Generate ID if not set
	if id, ok := record["ID"]; !ok || id == uint(0) {
		records := db.records[tableName]
		record["ID"] = uint(len(records) + 1)
	}
	
	newDB.records[tableName] = append(db.records[tableName], record)
	mapToStruct(record, value)
	
	newDB.RowsAffected = 1
	return newDB
}

// Save updates an existing record or creates a new one
func (db *DB) Save(value interface{}) *DB {
	newDB := db.clone()
	tableName := db.tableName
	if tableName == "" {
		tableName = getTableName(value)
	}
	
	record := structToMap(value)
	id := record["ID"]
	
	if id == nil || id == uint(0) {
		return db.Create(value)
	}
	
	records := db.records[tableName]
	found := false
	for i, r := range records {
		if r["ID"] == id {
			record["UpdatedAt"] = time.Now()
			if createdAt, ok := r["CreatedAt"]; ok {
				record["CreatedAt"] = createdAt
			}
			newDB.records[tableName][i] = record
			found = true
			newDB.RowsAffected = 1
			break
		}
	}
	
	if !found {
		newDB.Error = errors.New("record not found")
		return newDB
	}
	
	return newDB
}

// Update updates records with given attributes
func (db *DB) Update(column string, value interface{}) *DB {
	return db.Updates(map[string]interface{}{column: value})
}

// Updates updates records with given attributes
func (db *DB) Updates(values map[string]interface{}) *DB {
	newDB := db.clone()
	tableName := db.tableName
	
	records, exists := db.records[tableName]
	if !exists {
		newDB.RowsAffected = 0
		return newDB
	}
	
	filtered := db.getFilteredIndices(records)
	values["UpdatedAt"] = time.Now()
	
	for _, idx := range filtered {
		for k, v := range values {
			newDB.records[tableName][idx][k] = v
		}
	}
	
	newDB.RowsAffected = int64(len(filtered))
	return newDB
}

// Delete soft deletes records
func (db *DB) Delete(value interface{}) *DB {
	newDB := db.clone()
	tableName := db.tableName
	if tableName == "" && value != nil {
		tableName = getTableName(value)
	}
	
	records, exists := db.records[tableName]
	if !exists {
		newDB.RowsAffected = 0
		return newDB
	}
	
	filtered := db.getFilteredIndices(records)
	now := time.Now()
	
	for _, idx := range filtered {
		newDB.records[tableName][idx]["DeletedAt"] = &now
	}
	
	newDB.RowsAffected = int64(len(filtered))
	return newDB
}

// Unscoped removes the soft delete condition
func (db *DB) Unscoped() *DB {
	newDB := db.clone()
	// In a real implementation, this would modify query behavior
	// For this emulator, we'll just return the DB
	return newDB
}

// Limit sets the maximum number of records to retrieve
func (db *DB) Limit(limit int) *DB {
	newDB := db.clone()
	newDB.limit = limit
	return newDB
}

// Offset sets the number of records to skip
func (db *DB) Offset(offset int) *DB {
	newDB := db.clone()
	newDB.offset = offset
	return newDB
}

// Order specifies the order when retrieving records
func (db *DB) Order(value string) *DB {
	newDB := db.clone()
	newDB.order = value
	return newDB
}

// Count counts the number of records
func (db *DB) Count(count *int64) *DB {
	newDB := db.clone()
	tableName := db.tableName
	
	records, exists := db.records[tableName]
	if !exists {
		*count = 0
		return newDB
	}
	
	filtered := db.applyFilters(records)
	*count = int64(len(filtered))
	return newDB
}

// Raw executes raw SQL
func (db *DB) Raw(sql string, values ...interface{}) *DB {
	newDB := db.clone()
	// Simulated raw SQL execution
	return newDB
}

// Exec executes raw SQL that doesn't return rows
func (db *DB) Exec(sql string, values ...interface{}) *DB {
	newDB := db.clone()
	// Simulated execution
	newDB.RowsAffected = 1
	return newDB
}

// Begin starts a transaction
func (db *DB) Begin() *DB {
	newDB := db.clone()
	// Transaction simulation
	return newDB
}

// Commit commits a transaction
func (db *DB) Commit() *DB {
	return db
}

// Rollback rolls back a transaction
func (db *DB) Rollback() *DB {
	return db
}

// Helper functions

func (db *DB) clone() *DB {
	return &DB{
		records:   db.records,
		tableName: db.tableName,
		where:     append([]whereClause{}, db.where...),
		limit:     db.limit,
		offset:    db.offset,
		order:     db.order,
	}
}

func (db *DB) applyFilters(records []map[string]interface{}) []map[string]interface{} {
	filtered := []map[string]interface{}{}
	
	for _, record := range records {
		// Skip soft deleted records by default
		if deletedAt, ok := record["DeletedAt"]; ok && deletedAt != nil {
			continue
		}
		
		if db.matchesWhere(record) {
			filtered = append(filtered, record)
		}
	}
	
	// Apply offset and limit
	if db.offset > 0 && db.offset < len(filtered) {
		filtered = filtered[db.offset:]
	} else if db.offset >= len(filtered) {
		filtered = []map[string]interface{}{}
	}
	
	if db.limit > 0 && db.limit < len(filtered) {
		filtered = filtered[:db.limit]
	}
	
	return filtered
}

func (db *DB) getFilteredIndices(records []map[string]interface{}) []int {
	indices := []int{}
	
	for i, record := range records {
		// Skip soft deleted records by default
		if deletedAt, ok := record["DeletedAt"]; ok && deletedAt != nil {
			continue
		}
		
		if db.matchesWhere(record) {
			indices = append(indices, i)
		}
	}
	
	return indices
}

func (db *DB) matchesWhere(record map[string]interface{}) bool {
	if len(db.where) == 0 {
		return true
	}
	
	for _, clause := range db.where {
		if !evaluateCondition(record, clause.condition, clause.args) {
			return false
		}
	}
	
	return true
}

func evaluateCondition(record map[string]interface{}, condition string, args []interface{}) bool {
	// For ID-based queries
	if (condition == "id = ?" || condition == "ID = ?") && len(args) > 0 {
		recordID := fmt.Sprintf("%v", record["ID"])
		argID := fmt.Sprintf("%v", args[0])
		return recordID == argID
	}
	
	// Simple condition parsing
	if strings.Contains(condition, "=") {
		parts := strings.Split(condition, "=")
		if len(parts) == 2 {
			field := strings.TrimSpace(parts[0])
			value := record[field]
			if len(args) > 0 {
				return fmt.Sprintf("%v", value) == fmt.Sprintf("%v", args[0])
			}
		}
	}
	
	return true
}

func getTableName(value interface{}) string {
	t := reflect.TypeOf(value)
	if t.Kind() == reflect.Ptr {
		t = t.Elem()
	}
	if t.Kind() == reflect.Slice {
		t = t.Elem()
	}
	if t.Kind() == reflect.Ptr {
		t = t.Elem()
	}
	
	name := t.Name()
	return strings.ToLower(name) + "s"
}

func structToMap(value interface{}) map[string]interface{} {
	result := make(map[string]interface{})
	
	v := reflect.ValueOf(value)
	if v.Kind() == reflect.Ptr {
		v = v.Elem()
	}
	
	t := v.Type()
	for i := 0; i < v.NumField(); i++ {
		field := t.Field(i)
		fieldValue := v.Field(i)
		
		if fieldValue.CanInterface() {
			result[field.Name] = fieldValue.Interface()
		}
	}
	
	return result
}

func mapToStruct(m map[string]interface{}, dest interface{}) {
	v := reflect.ValueOf(dest)
	if v.Kind() != reflect.Ptr {
		return
	}
	
	v = v.Elem()
	t := v.Type()
	
	for i := 0; i < v.NumField(); i++ {
		field := t.Field(i)
		if value, ok := m[field.Name]; ok {
			fieldValue := v.Field(i)
			if fieldValue.CanSet() {
				val := reflect.ValueOf(value)
				if val.Type().AssignableTo(fieldValue.Type()) {
					fieldValue.Set(val)
				}
			}
		}
	}
}

// AutoMigrate runs auto migration for given models
func (db *DB) AutoMigrate(models ...interface{}) error {
	for _, model := range models {
		tableName := getTableName(model)
		if _, exists := db.records[tableName]; !exists {
			db.records[tableName] = []map[string]interface{}{}
		}
	}
	return nil
}
