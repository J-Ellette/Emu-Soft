using System;
using System.Threading.Tasks;
using ViperNet;

namespace ViperNetTests
{
    public class TestViperNet
    {
        public static async Task Main(string[] args)
        {
            Console.WriteLine("=== ViperNet (ASP.NET Core Emulator) Tests ===\n");

            // Test 1: Basic Web Application Creation
            Console.WriteLine("Test 1: Basic Web Application Creation");
            Console.WriteLine("---------------------------------------");
            var builder = WebApplicationFactory.CreateBuilder(args);
            var app = builder.Build();
            Console.WriteLine("✓ Web application created successfully");
            Console.WriteLine($"✓ Environment: {app.Environment.EnvironmentName}");
            Console.WriteLine();

            // Test 2: Service Registration
            Console.WriteLine("Test 2: Service Registration");
            Console.WriteLine("----------------------------");
            var builder2 = WebApplicationFactory.CreateBuilder();
            builder2.Services.AddSingleton<ITestService, TestService>();
            builder2.Services.AddScoped<ITestService, TestService>();
            builder2.Services.AddTransient<ITestService, TestService>();
            builder2.Services.AddControllers();
            builder2.Services.AddCors(options =>
            {
                options.AddPolicy("AllowAll", policy =>
                {
                    policy.AllowAnyOrigin()
                          .AllowAnyMethod()
                          .AllowAnyHeader();
                });
            });
            Console.WriteLine($"✓ Registered {builder2.Services.Count} services");
            Console.WriteLine();

            // Test 3: Endpoint Mapping
            Console.WriteLine("Test 3: Endpoint Mapping");
            Console.WriteLine("------------------------");
            var builder3 = WebApplicationFactory.CreateBuilder();
            var app3 = builder3.Build();
            
            app3.MapGet("/", async (HttpContext ctx) =>
            {
                await ctx.Response.WriteAsync("Hello World!");
            });
            
            app3.MapGet("/api/users", async (HttpContext ctx) =>
            {
                await ctx.Response.WriteAsJsonAsync(new { message = "User list" });
            });
            
            app3.MapPost("/api/users", async (HttpContext ctx) =>
            {
                await ctx.Response.WriteAsJsonAsync(new { message = "User created" });
            });
            
            app3.MapPut("/api/users/1", async (HttpContext ctx) =>
            {
                await ctx.Response.WriteAsJsonAsync(new { message = "User updated" });
            });
            
            app3.MapDelete("/api/users/1", async (HttpContext ctx) =>
            {
                await ctx.Response.WriteAsync("User deleted");
            });
            
            Console.WriteLine("✓ Mapped 5 endpoints");
            Console.WriteLine();

            // Test 4: Middleware
            Console.WriteLine("Test 4: Middleware Configuration");
            Console.WriteLine("---------------------------------");
            var builder4 = WebApplicationFactory.CreateBuilder();
            var app4 = builder4.Build();
            
            app4.UseRouting();
            app4.UseAuthentication();
            app4.UseAuthorization();
            app4.UseCors("AllowAll");
            app4.UseHttpsRedirection();
            app4.UseStaticFiles();
            
            app4.Use(async (context, next) =>
            {
                Console.WriteLine("Custom middleware executed");
                await next();
            });
            
            Console.WriteLine("✓ Middleware pipeline configured");
            Console.WriteLine();

            // Test 5: Configuration
            Console.WriteLine("Test 5: Configuration Management");
            Console.WriteLine("--------------------------------");
            var builder5 = WebApplicationFactory.CreateBuilder();
            builder5.Configuration["AppName"] = "ViperNet Test";
            builder5.Configuration["ConnectionStrings:DefaultConnection"] = "Server=localhost;Database=test";
            var app5 = builder5.Build();
            
            Console.WriteLine($"✓ AppName: {app5.Configuration["AppName"]}");
            Console.WriteLine($"✓ Connection String: {app5.Configuration.GetConnectionString("DefaultConnection")}");
            Console.WriteLine();

            // Test 6: HTTP Context
            Console.WriteLine("Test 6: HTTP Context");
            Console.WriteLine("--------------------");
            var context = new HttpContext();
            context.Request.Method = "GET";
            context.Request.Path = "/api/test";
            context.Request.Headers["Authorization"] = "Bearer token123";
            context.Request.Query["page"] = "1";
            context.Request.Query["size"] = "10";
            
            Console.WriteLine($"✓ Method: {context.Request.Method}");
            Console.WriteLine($"✓ Path: {context.Request.Path}");
            Console.WriteLine($"✓ Authorization Header: {context.Request.Headers["Authorization"]}");
            Console.WriteLine($"✓ Query Params: page={context.Request.Query["page"]}, size={context.Request.Query["size"]}");
            Console.WriteLine();

            // Test 7: Action Results
            Console.WriteLine("Test 7: Controller Action Results");
            Console.WriteLine("----------------------------------");
            var controller = new TestController();
            
            var okResult = controller.Ok();
            Console.WriteLine($"✓ OkResult: Status {okResult.StatusCode}");
            
            var okObjectResult = controller.Ok(new { id = 1, name = "Test" });
            Console.WriteLine($"✓ OkObjectResult: Status {okObjectResult.StatusCode}");
            
            var badRequestResult = controller.BadRequest();
            Console.WriteLine($"✓ BadRequestResult: Status {badRequestResult.StatusCode}");
            
            var notFoundResult = controller.NotFound();
            Console.WriteLine($"✓ NotFoundResult: Status {notFoundResult.StatusCode}");
            
            var createdResult = controller.Created("/api/users/1", new { id = 1 });
            Console.WriteLine($"✓ CreatedResult: Status {createdResult.StatusCode}, Location: {createdResult.Uri}");
            
            var noContentResult = controller.NoContent();
            Console.WriteLine($"✓ NoContentResult: Status {noContentResult.StatusCode}");
            Console.WriteLine();

            // Test 8: Run Application
            Console.WriteLine("Test 8: Running Application");
            Console.WriteLine("---------------------------");
            var builder8 = WebApplicationFactory.CreateBuilder();
            builder8.Services.AddControllers();
            var app8 = builder8.Build();
            app8.MapControllers();
            
            app8.MapGet("/", async (HttpContext ctx) =>
            {
                await ctx.Response.WriteAsync("Welcome to ViperNet!");
            });
            
            await app8.RunAsync("http://localhost:5000");
            Console.WriteLine();

            // Test 9: Environment
            Console.WriteLine("Test 9: Web Host Environment");
            Console.WriteLine("----------------------------");
            var builder9 = WebApplicationFactory.CreateBuilder();
            builder9.Environment.EnvironmentName = "Production";
            builder9.Environment.ApplicationName = "ViperNet API";
            var app9 = builder9.Build();
            
            Console.WriteLine($"✓ Environment Name: {app9.Environment.EnvironmentName}");
            Console.WriteLine($"✓ Application Name: {app9.Environment.ApplicationName}");
            Console.WriteLine($"✓ Content Root Path: {app9.Environment.ContentRootPath}");
            Console.WriteLine();

            // Test 10: Disposal
            Console.WriteLine("Test 10: Resource Disposal");
            Console.WriteLine("--------------------------");
            using (var app10 = WebApplicationFactory.CreateBuilder().Build())
            {
                Console.WriteLine("✓ Application created in using block");
            }
            Console.WriteLine("✓ Application disposed");
            Console.WriteLine();

            Console.WriteLine("=== All Tests Completed Successfully ===");
        }
    }

    // Test interfaces and classes
    public interface ITestService
    {
        string GetData();
    }

    public class TestService : ITestService
    {
        public string GetData()
        {
            return "Test Data";
        }
    }

    [ApiController]
    [Route("api/[controller]")]
    public class TestController : ControllerBase
    {
        [HttpGet]
        public OkObjectResult GetAll()
        {
            return Ok(new[] { "Item1", "Item2", "Item3" });
        }

        [HttpGet("{id}")]
        public ActionResult GetById([FromRoute] int id)
        {
            if (id > 0)
                return Ok(new { id, name = "Test Item" });
            return NotFound();
        }

        [HttpPost]
        public CreatedResult Create([FromBody] object data)
        {
            return Created("/api/test/1", new { id = 1 });
        }

        [HttpPut("{id}")]
        public OkResult Update([FromRoute] int id, [FromBody] object data)
        {
            return Ok();
        }

        [HttpDelete("{id}")]
        public NoContentResult Delete([FromRoute] int id)
        {
            return NoContent();
        }
    }
}
