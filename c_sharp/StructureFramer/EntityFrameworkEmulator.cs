/**
 * Developed by PowerShield, as an alternative to Entity Framework
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;

namespace EntityFrameworkEmulator
{
    // Entity base class
    public abstract class Entity
    {
        public int Id { get; set; }
    }

    // DbContext - Core of Entity Framework
    public abstract class DbContext : IDisposable
    {
        private readonly Dictionary<Type, object> _sets = new Dictionary<Type, object>();
        private readonly List<object> _trackedEntities = new List<object>();
        private readonly Dictionary<object, EntityState> _entityStates = new Dictionary<object, EntityState>();
        
        public DbContext()
        {
            // Initialize
        }

        public DbSet<TEntity> Set<TEntity>() where TEntity : class
        {
            var type = typeof(TEntity);
            if (!_sets.ContainsKey(type))
            {
                _sets[type] = new DbSet<TEntity>(this);
            }
            return (DbSet<TEntity>)_sets[type];
        }

        public void Add<TEntity>(TEntity entity) where TEntity : class
        {
            if (!_trackedEntities.Contains(entity))
            {
                _trackedEntities.Add(entity);
                _entityStates[entity] = EntityState.Added;
            }
        }

        public void Update<TEntity>(TEntity entity) where TEntity : class
        {
            if (!_trackedEntities.Contains(entity))
            {
                _trackedEntities.Add(entity);
            }
            _entityStates[entity] = EntityState.Modified;
        }

        public void Remove<TEntity>(TEntity entity) where TEntity : class
        {
            if (!_trackedEntities.Contains(entity))
            {
                _trackedEntities.Add(entity);
            }
            _entityStates[entity] = EntityState.Deleted;
        }

        public int SaveChanges()
        {
            int changes = 0;
            
            foreach (var entity in _trackedEntities.ToList())
            {
                if (_entityStates.TryGetValue(entity, out var state))
                {
                    switch (state)
                    {
                        case EntityState.Added:
                            Console.WriteLine($"[EF] INSERT: {entity.GetType().Name}");
                            changes++;
                            break;
                        case EntityState.Modified:
                            Console.WriteLine($"[EF] UPDATE: {entity.GetType().Name}");
                            changes++;
                            break;
                        case EntityState.Deleted:
                            Console.WriteLine($"[EF] DELETE: {entity.GetType().Name}");
                            changes++;
                            break;
                    }
                }
            }

            // Clear tracking after save
            _trackedEntities.Clear();
            _entityStates.Clear();
            
            return changes;
        }

        public void Dispose()
        {
            // Cleanup
            _sets.Clear();
            _trackedEntities.Clear();
            _entityStates.Clear();
        }
    }

    // DbSet - Collection of entities
    public class DbSet<TEntity> : IQueryable<TEntity> where TEntity : class
    {
        private readonly DbContext _context;
        private readonly List<TEntity> _data = new List<TEntity>();
        private IQueryable<TEntity> _query;

        public DbSet(DbContext context)
        {
            _context = context;
            _query = _data.AsQueryable();
        }

        public void Add(TEntity entity)
        {
            _data.Add(entity);
            _context.Add(entity);
        }

        public void Update(TEntity entity)
        {
            _context.Update(entity);
        }

        public void Remove(TEntity entity)
        {
            _data.Remove(entity);
            _context.Remove(entity);
        }

        public TEntity Find(params object[] keyValues)
        {
            if (keyValues.Length == 0) return null;
            
            var id = keyValues[0];
            return _data.FirstOrDefault(e => 
            {
                var prop = e.GetType().GetProperty("Id");
                return prop?.GetValue(e)?.Equals(id) ?? false;
            });
        }

        // IQueryable implementation
        public Type ElementType => _query.ElementType;
        public Expression Expression => _query.Expression;
        public IQueryProvider Provider => _query.Provider;
        public IEnumerator<TEntity> GetEnumerator() => _query.GetEnumerator();
        System.Collections.IEnumerator System.Collections.IEnumerable.GetEnumerator() => GetEnumerator();
    }

    // Entity State enum
    public enum EntityState
    {
        Detached,
        Unchanged,
        Added,
        Deleted,
        Modified
    }

    // Migration base class
    public abstract class Migration
    {
        protected MigrationBuilder MigrationBuilder { get; set; }

        public Migration()
        {
            MigrationBuilder = new MigrationBuilder();
        }

        public abstract void Up();
        public abstract void Down();
    }

    // Migration Builder
    public class MigrationBuilder
    {
        public void CreateTable(string name, Action<TableBuilder> buildAction)
        {
            Console.WriteLine($"[Migration] Creating table: {name}");
            var builder = new TableBuilder(name);
            buildAction(builder);
        }

        public void DropTable(string name)
        {
            Console.WriteLine($"[Migration] Dropping table: {name}");
        }

        public void AddColumn(string table, string column, string type)
        {
            Console.WriteLine($"[Migration] Adding column {column} to {table}");
        }

        public void DropColumn(string table, string column)
        {
            Console.WriteLine($"[Migration] Dropping column {column} from {table}");
        }
    }

    // Table Builder for migrations
    public class TableBuilder
    {
        public string TableName { get; }
        private List<string> _columns = new List<string>();

        public TableBuilder(string tableName)
        {
            TableName = tableName;
        }

        public TableBuilder Column(string name, string type, bool nullable = false, bool primaryKey = false)
        {
            var columnDef = $"{name} {type}";
            if (!nullable) columnDef += " NOT NULL";
            if (primaryKey) columnDef += " PRIMARY KEY";
            
            _columns.Add(columnDef);
            Console.WriteLine($"  - Column: {columnDef}");
            return this;
        }

        public TableBuilder PrimaryKey(string columnName)
        {
            Console.WriteLine($"  - Primary Key: {columnName}");
            return this;
        }

        public TableBuilder ForeignKey(string columnName, string referencedTable, string referencedColumn)
        {
            Console.WriteLine($"  - Foreign Key: {columnName} -> {referencedTable}.{referencedColumn}");
            return this;
        }
    }

    // Model Builder for Fluent API
    public class ModelBuilder
    {
        private readonly Dictionary<Type, object> _entityConfigurations = new Dictionary<Type, object>();

        public EntityTypeBuilder<TEntity> Entity<TEntity>() where TEntity : class
        {
            var type = typeof(TEntity);
            if (!_entityConfigurations.ContainsKey(type))
            {
                _entityConfigurations[type] = new EntityTypeBuilder<TEntity>();
            }
            return (EntityTypeBuilder<TEntity>)_entityConfigurations[type];
        }
    }

    // Entity Type Builder for Fluent API
    public class EntityTypeBuilder<TEntity> where TEntity : class
    {
        private string _tableName;
        private string _primaryKey;
        private readonly List<string> _indexes = new List<string>();

        public EntityTypeBuilder<TEntity> ToTable(string tableName)
        {
            _tableName = tableName;
            Console.WriteLine($"[Configuration] {typeof(TEntity).Name} mapped to table: {tableName}");
            return this;
        }

        public EntityTypeBuilder<TEntity> HasKey(Expression<Func<TEntity, object>> keyExpression)
        {
            // Extract property name from expression
            var memberExpr = keyExpression.Body as MemberExpression;
            if (memberExpr == null && keyExpression.Body is UnaryExpression unary)
            {
                memberExpr = unary.Operand as MemberExpression;
            }
            
            if (memberExpr != null)
            {
                _primaryKey = memberExpr.Member.Name;
                Console.WriteLine($"[Configuration] Primary key: {_primaryKey}");
            }
            return this;
        }

        public EntityTypeBuilder<TEntity> HasIndex(Expression<Func<TEntity, object>> indexExpression)
        {
            var memberExpr = indexExpression.Body as MemberExpression;
            if (memberExpr == null && indexExpression.Body is UnaryExpression unary)
            {
                memberExpr = unary.Operand as MemberExpression;
            }
            
            if (memberExpr != null)
            {
                var indexName = memberExpr.Member.Name;
                _indexes.Add(indexName);
                Console.WriteLine($"[Configuration] Index on: {indexName}");
            }
            return this;
        }

        public PropertyBuilder<TProperty> Property<TProperty>(Expression<Func<TEntity, TProperty>> propertyExpression)
        {
            var memberExpr = propertyExpression.Body as MemberExpression;
            if (memberExpr == null && propertyExpression.Body is UnaryExpression unary)
            {
                memberExpr = unary.Operand as MemberExpression;
            }
            
            return new PropertyBuilder<TProperty>(memberExpr?.Member.Name ?? "Unknown");
        }

        public ReferenceNavigationBuilder<TEntity, TRelatedEntity> HasOne<TRelatedEntity>(
            Expression<Func<TEntity, TRelatedEntity>> navigationExpression) where TRelatedEntity : class
        {
            return new ReferenceNavigationBuilder<TEntity, TRelatedEntity>();
        }

        public CollectionNavigationBuilder<TEntity, TRelatedEntity> HasMany<TRelatedEntity>(
            Expression<Func<TEntity, IEnumerable<TRelatedEntity>>> navigationExpression) where TRelatedEntity : class
        {
            return new CollectionNavigationBuilder<TEntity, TRelatedEntity>();
        }
    }

    // Property Builder for Fluent API
    public class PropertyBuilder<TProperty>
    {
        private readonly string _propertyName;

        public PropertyBuilder(string propertyName)
        {
            _propertyName = propertyName;
        }

        public PropertyBuilder<TProperty> IsRequired()
        {
            Console.WriteLine($"[Configuration] Property {_propertyName} is required");
            return this;
        }

        public PropertyBuilder<TProperty> HasMaxLength(int length)
        {
            Console.WriteLine($"[Configuration] Property {_propertyName} max length: {length}");
            return this;
        }

        public PropertyBuilder<TProperty> HasColumnName(string columnName)
        {
            Console.WriteLine($"[Configuration] Property {_propertyName} mapped to column: {columnName}");
            return this;
        }

        public PropertyBuilder<TProperty> HasDefaultValue(TProperty value)
        {
            Console.WriteLine($"[Configuration] Property {_propertyName} default value: {value}");
            return this;
        }
    }

    // Navigation builders for relationships
    public class ReferenceNavigationBuilder<TEntity, TRelatedEntity> 
        where TEntity : class 
        where TRelatedEntity : class
    {
        public ReferenceNavigationBuilder<TEntity, TRelatedEntity> WithMany(
            Expression<Func<TRelatedEntity, IEnumerable<TEntity>>> navigationExpression = null)
        {
            Console.WriteLine($"[Configuration] One-to-Many relationship");
            return this;
        }

        public ReferenceNavigationBuilder<TEntity, TRelatedEntity> WithOne(
            Expression<Func<TRelatedEntity, TEntity>> navigationExpression = null)
        {
            Console.WriteLine($"[Configuration] One-to-One relationship");
            return this;
        }

        public ReferenceNavigationBuilder<TEntity, TRelatedEntity> HasForeignKey<TKey>(
            Expression<Func<TEntity, TKey>> foreignKeyExpression)
        {
            Console.WriteLine($"[Configuration] Foreign key configured");
            return this;
        }
    }

    public class CollectionNavigationBuilder<TEntity, TRelatedEntity>
        where TEntity : class
        where TRelatedEntity : class
    {
        public CollectionNavigationBuilder<TEntity, TRelatedEntity> WithOne(
            Expression<Func<TRelatedEntity, TEntity>> navigationExpression = null)
        {
            Console.WriteLine($"[Configuration] Many-to-One relationship");
            return this;
        }

        public CollectionNavigationBuilder<TEntity, TRelatedEntity> WithMany(
            Expression<Func<TRelatedEntity, IEnumerable<TEntity>>> navigationExpression = null)
        {
            Console.WriteLine($"[Configuration] Many-to-Many relationship");
            return this;
        }
    }

    // LINQ extension methods for EF
    public static class EntityFrameworkQueryableExtensions
    {
        public static IQueryable<TEntity> Include<TEntity, TProperty>(
            this IQueryable<TEntity> source,
            Expression<Func<TEntity, TProperty>> navigationPropertyPath) 
            where TEntity : class
        {
            Console.WriteLine("[EF] Including related entities (eager loading)");
            return source;
        }

        public static IQueryable<TEntity> AsNoTracking<TEntity>(
            this IQueryable<TEntity> source) 
            where TEntity : class
        {
            Console.WriteLine("[EF] Query set to no-tracking");
            return source;
        }
    }
}
