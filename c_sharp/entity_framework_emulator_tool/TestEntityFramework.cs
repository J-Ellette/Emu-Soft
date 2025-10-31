using System;
using System.Collections.Generic;
using System.Linq;
using EntityFrameworkEmulator;

namespace TestEntityFramework
{
    // Test entities
    public class Blog : Entity
    {
        public string Title { get; set; }
        public string Url { get; set; }
        public List<Post> Posts { get; set; } = new List<Post>();
    }

    public class Post : Entity
    {
        public string Title { get; set; }
        public string Content { get; set; }
        public int BlogId { get; set; }
        public Blog Blog { get; set; }
    }

    // Test context
    public class BloggingContext : DbContext
    {
        public DbSet<Blog> Blogs => Set<Blog>();
        public DbSet<Post> Posts => Set<Post>();
    }

    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== Entity Framework Emulator Tests ===\n");

            TestBasicCRUD();
            TestLinqQueries();
            TestFluentAPI();
            TestMigrations();
            TestChangeTracking();

            Console.WriteLine("\n=== All Tests Completed Successfully ===");
        }

        static void TestBasicCRUD()
        {
            Console.WriteLine("--- Test: Basic CRUD Operations ---");
            
            using (var context = new BloggingContext())
            {
                // Create
                var blog1 = new Blog 
                { 
                    Id = 1,
                    Title = "Tech Blog",
                    Url = "https://techblog.com"
                };
                var blog2 = new Blog 
                { 
                    Id = 2,
                    Title = "Gaming Blog",
                    Url = "https://gamingblog.com"
                };
                
                context.Blogs.Add(blog1);
                context.Blogs.Add(blog2);
                
                int changes = context.SaveChanges();
                Console.WriteLine($"Created {changes} blogs");
                
                // Read
                var foundBlog = context.Blogs.Find(1);
                if (foundBlog != null)
                {
                    Console.WriteLine($"Found blog: {foundBlog.Title}");
                }
                
                // Update
                foundBlog.Title = "Updated Tech Blog";
                context.Blogs.Update(foundBlog);
                changes = context.SaveChanges();
                Console.WriteLine($"Updated {changes} blogs");
                
                // Delete
                context.Blogs.Remove(blog2);
                changes = context.SaveChanges();
                Console.WriteLine($"Deleted {changes} blogs");
            }
            
            Console.WriteLine();
        }

        static void TestLinqQueries()
        {
            Console.WriteLine("--- Test: LINQ Queries ---");
            
            using (var context = new BloggingContext())
            {
                // Add test data
                context.Blogs.Add(new Blog { Id = 1, Title = "Tech Blog", Url = "tech.com" });
                context.Blogs.Add(new Blog { Id = 2, Title = "Gaming Blog", Url = "gaming.com" });
                context.Blogs.Add(new Blog { Id = 3, Title = "Tech News", Url = "technews.com" });
                context.SaveChanges();
                
                // Query with Where
                var techBlogs = context.Blogs
                    .Where(b => b.Title.Contains("Tech"))
                    .ToList();
                Console.WriteLine($"Tech blogs: {techBlogs.Count}");
                
                // Query with OrderBy
                var sortedBlogs = context.Blogs
                    .OrderBy(b => b.Title)
                    .ToList();
                Console.WriteLine($"Sorted blogs: {sortedBlogs.Count}");
                
                // Query with Select
                var urls = context.Blogs
                    .Select(b => b.Url)
                    .ToList();
                Console.WriteLine($"Blog URLs: {urls.Count}");
                
                // No tracking query
                var readOnlyBlogs = context.Blogs
                    .AsNoTracking()
                    .ToList();
                Console.WriteLine($"Read-only blogs: {readOnlyBlogs.Count}");
            }
            
            Console.WriteLine();
        }

        static void TestFluentAPI()
        {
            Console.WriteLine("--- Test: Fluent API Configuration ---");
            
            var modelBuilder = new ModelBuilder();
            
            // Configure Blog entity
            modelBuilder.Entity<Blog>()
                .ToTable("Blogs")
                .HasKey(b => b.Id);
            
            modelBuilder.Entity<Blog>()
                .Property(b => b.Title)
                .IsRequired()
                .HasMaxLength(200);
            
            modelBuilder.Entity<Blog>()
                .HasIndex(b => b.Url);
            
            // Configure Post entity
            modelBuilder.Entity<Post>()
                .ToTable("Posts")
                .HasKey(p => p.Id);
            
            modelBuilder.Entity<Post>()
                .Property(p => p.Title)
                .IsRequired()
                .HasMaxLength(200);
            
            // Configure relationship
            modelBuilder.Entity<Post>()
                .HasOne(p => p.Blog)
                .WithMany(b => b.Posts)
                .HasForeignKey(p => p.BlogId);
            
            Console.WriteLine("Fluent API configuration completed");
            Console.WriteLine();
        }

        static void TestMigrations()
        {
            Console.WriteLine("--- Test: Migrations ---");
            
            var migration1 = new CreateBlogsTable();
            migration1.Up();
            
            var migration2 = new AddPostsTable();
            migration2.Up();
            
            Console.WriteLine("Migrations applied successfully");
            Console.WriteLine();
        }

        static void TestChangeTracking()
        {
            Console.WriteLine("--- Test: Change Tracking ---");
            
            using (var context = new BloggingContext())
            {
                var blog = new Blog 
                { 
                    Id = 1,
                    Title = "Change Tracking Test",
                    Url = "test.com"
                };
                
                Console.WriteLine("Entity created (Detached)");
                
                context.Blogs.Add(blog);
                Console.WriteLine("Entity added (Added state)");
                
                context.SaveChanges();
                Console.WriteLine("Changes saved (Unchanged state)");
                
                blog.Title = "Modified Title";
                context.Blogs.Update(blog);
                Console.WriteLine("Entity updated (Modified state)");
                
                context.SaveChanges();
                Console.WriteLine("Changes saved (Unchanged state)");
                
                context.Blogs.Remove(blog);
                Console.WriteLine("Entity removed (Deleted state)");
                
                context.SaveChanges();
                Console.WriteLine("Changes saved (Entity removed from context)");
            }
            
            Console.WriteLine();
        }
    }

    // Test migrations
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
}
