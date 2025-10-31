# Entity Framework Emulator - ORM for .NET

A lightweight emulation of **Entity Framework**, Microsoft's object-relational mapping (ORM) framework for .NET that enables developers to work with databases using .NET objects.

## Features

This emulator implements core Entity Framework functionality:

### DbContext
- **Database Context**: Central class for database operations
- **DbSet<T>**: Represent collections of entities
- **Change Tracking**: Track entity state changes
- **SaveChanges**: Persist changes to database
- **Dispose Pattern**: Proper resource cleanup

### Entity Management
- **Add**: Add new entities
- **Update**: Modify existing entities
- **Remove**: Delete entities
- **Find**: Find entities by primary key
- **Entity States**: Added, Modified, Deleted, Unchanged, Detached

### Querying
- **LINQ Support**: Query entities using LINQ
- **IQueryable Interface**: Full LINQ query capabilities
- **Include**: Eager loading of related entities
- **AsNoTracking**: Read-only queries for performance
- **Where, Select, OrderBy**: Standard LINQ operations

### Fluent API Configuration
- **ModelBuilder**: Configure entity models
- **EntityTypeBuilder**: Configure individual entities
- **ToTable**: Map entities to tables
- **HasKey**: Define primary keys
- **HasIndex**: Create indexes
- **Property Configuration**: Required, MaxLength, DefaultValue
- **Relationships**: One-to-One, One-to-Many, Many-to-Many

### Migrations
- **Migration Base Class**: Create database migrations
- **MigrationBuilder**: Build migration operations
- **CreateTable/DropTable**: Table operations
- **AddColumn/DropColumn**: Column operations
- **Up/Down Methods**: Forward and rollback migrations

## What It Emulates

This tool emulates [Entity Framework Core](https://docs.microsoft.com/en-us/ef/core/), Microsoft's modern ORM framework used in millions of .NET applications.

### Core Components Implemented

1. **DbContext**
   - Database context management
   - Change tracking
   - Save changes operation

2. **DbSet<T>**
   - Entity collections
   - CRUD operations
   - LINQ query support

3. **Fluent API**
   - Entity configuration
   - Relationship mapping
   - Property constraints

4. **Migrations**
   - Schema evolution
   - Up/Down operations
   - Table and column management

## Usage

### Define Entities

```csharp
using EntityFrameworkEmulator;

public class Blog : Entity
{
    public string Title { get; set; }
    public string Url { get; set; }
    public List<Post> Posts { get; set; }
}

public class Post : Entity
{
    public string Title { get; set; }
    public string Content { get; set; }
    public int BlogId { get; set; }
    public Blog Blog { get; set; }
}
```

### Create DbContext

```csharp
public class BloggingContext : DbContext
{
    public DbSet<Blog> Blogs { get; set; }
    public DbSet<Post> Posts { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Configure entities using Fluent API
        modelBuilder.Entity<Blog>()
            .ToTable("Blogs")
            .HasKey(b => b.Id);

        modelBuilder.Entity<Blog>()
            .Property(b => b.Title)
            .IsRequired()
            .HasMaxLength(200);

        modelBuilder.Entity<Post>()
            .ToTable("Posts")
            .HasKey(p => p.Id);

        modelBuilder.Entity<Post>()
            .HasOne(p => p.Blog)
            .WithMany(b => b.Posts)
            .HasForeignKey(p => p.BlogId);
    }
}
```

### Basic CRUD Operations

```csharp
using (var context = new BloggingContext())
{
    // Create
    var blog = new Blog 
    { 
        Title = "My Blog",
        Url = "https://myblog.com"
    };
    context.Blogs.Add(blog);
    context.SaveChanges();

    // Read
    var blogs = context.Blogs.ToList();
    var foundBlog = context.Blogs.Find(1);

    // Update
    foundBlog.Title = "Updated Title";
    context.Blogs.Update(foundBlog);
    context.SaveChanges();

    // Delete
    context.Blogs.Remove(foundBlog);
    context.SaveChanges();
}
```

### LINQ Queries

```csharp
using (var context = new BloggingContext())
{
    // Simple query
    var blogs = context.Blogs
        .Where(b => b.Title.Contains("Tech"))
        .OrderBy(b => b.Title)
        .ToList();

    // Query with related data (eager loading)
    var blogsWithPosts = context.Blogs
        .Include(b => b.Posts)
        .ToList();

    // No-tracking query (read-only, faster)
    var readOnlyBlogs = context.Blogs
        .AsNoTracking()
        .Where(b => b.Url.Contains(".com"))
        .ToList();

    // Complex query
    var recentPosts = context.Posts
        .Where(p => p.CreatedDate > DateTime.Now.AddDays(-7))
        .OrderByDescending(p => p.CreatedDate)
        .Select(p => new { p.Title, p.Blog.Title })
        .Take(10)
        .ToList();
}
```

### Fluent API Configuration

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    // Table mapping
    modelBuilder.Entity<Blog>()
        .ToTable("tbl_blogs");

    // Primary key
    modelBuilder.Entity<Blog>()
        .HasKey(b => b.Id);

    // Index
    modelBuilder.Entity<Blog>()
        .HasIndex(b => b.Url);

    // Property constraints
    modelBuilder.Entity<Blog>()
        .Property(b => b.Title)
        .IsRequired()
        .HasMaxLength(200)
        .HasColumnName("blog_title");

    // One-to-Many relationship
    modelBuilder.Entity<Post>()
        .HasOne(p => p.Blog)
        .WithMany(b => b.Posts)
        .HasForeignKey(p => p.BlogId);

    // One-to-One relationship
    modelBuilder.Entity<BlogMetadata>()
        .HasOne(m => m.Blog)
        .WithOne(b => b.Metadata)
        .HasForeignKey<BlogMetadata>(m => m.BlogId);
}
```

### Migrations

```csharp
public class CreateBlogsTable : Migration
{
    public override void Up()
    {
        MigrationBuilder.CreateTable("Blogs", table =>
        {
            table.Column("Id", "INTEGER", primaryKey: true);
            table.Column("Title", "NVARCHAR(200)", nullable: false);
            table.Column("Url", "NVARCHAR(500)");
            table.PrimaryKey("Id");
        });
    }

    public override void Down()
    {
        MigrationBuilder.DropTable("Blogs");
    }
}

public class AddPostsTable : Migration
{
    public override void Up()
    {
        MigrationBuilder.CreateTable("Posts", table =>
        {
            table.Column("Id", "INTEGER", primaryKey: true);
            table.Column("Title", "NVARCHAR(200)", nullable: false);
            table.Column("Content", "NTEXT");
            table.Column("BlogId", "INTEGER");
            table.ForeignKey("BlogId", "Blogs", "Id");
        });
    }

    public override void Down()
    {
        MigrationBuilder.DropTable("Posts");
    }
}

// Run migrations
var migration1 = new CreateBlogsTable();
migration1.Up();

var migration2 = new AddPostsTable();
migration2.Up();
```

### Change Tracking

```csharp
using (var context = new BloggingContext())
{
    var blog = new Blog { Title = "New Blog" };
    
    // Entity state: Detached (not tracked)
    
    context.Blogs.Add(blog);
    // Entity state: Added
    
    context.SaveChanges();
    // Entity state: Unchanged
    
    blog.Title = "Updated Blog";
    context.Blogs.Update(blog);
    // Entity state: Modified
    
    context.SaveChanges();
    // Entity state: Unchanged
    
    context.Blogs.Remove(blog);
    // Entity state: Deleted
    
    context.SaveChanges();
    // Entity removed from context
}
```

## Testing

```bash
dotnet test
```

Or compile and run the test file:

```bash
csc /out:test.exe EntityFrameworkEmulator.cs TestEntityFramework.cs
./test.exe
```

## Use Cases

1. **Learning EF Core**: Understand Entity Framework concepts
2. **Development**: Develop without database setup
3. **Testing**: Unit test data access layer
4. **Education**: Teaching ORM concepts
5. **Prototyping**: Rapid application prototyping
6. **Migration Planning**: Plan database migrations

## Key Differences from Real Entity Framework

1. **No Database**: Doesn't connect to actual databases
2. **In-Memory Storage**: Data stored in memory only
3. **Simplified Tracking**: Change tracking is simplified
4. **No SQL Generation**: SQL is not actually generated
5. **Limited LINQ**: Some advanced LINQ operations may not work
6. **No Lazy Loading**: Lazy loading not implemented
7. **No Transactions**: Transaction support not included
8. **Simplified Migrations**: Migration operations are logged only

## Entity Framework Concepts

### DbContext
The primary class for interacting with a database. Manages entity objects during runtime, handles change tracking, and provides SaveChanges to persist data.

### DbSet<T>
Represents a collection of entities of a specific type. Provides methods for querying and saving entity data.

### Entity
A class that maps to a database table. Each instance represents a row in the table.

### Change Tracking
EF tracks changes made to entities. When SaveChanges is called, EF generates SQL commands to update the database.

### Fluent API
An alternative to data annotations for configuring entity models. Provides more flexibility and keeps configuration separate from entity classes.

### Migrations
A way to keep the database schema in sync with the entity model. Migrations can be applied forward (Up) or rolled back (Down).

## License

Educational emulator for learning purposes.

## References

- [Entity Framework Core Documentation](https://docs.microsoft.com/en-us/ef/core/)
- [EF Core GitHub](https://github.com/dotnet/efcore)
- [Fluent API](https://docs.microsoft.com/en-us/ef/core/modeling/)
- [Migrations](https://docs.microsoft.com/en-us/ef/core/managing-schemas/migrations/)
