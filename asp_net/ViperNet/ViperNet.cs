/**
 * Developed by PowerShield, as an alternative to ASP.NET Core
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Text.Json;
using System.IO;

namespace ViperNet
{
    // WebApplication builder and host
    public class WebApplicationBuilder
    {
        public IServiceCollection Services { get; }
        public ConfigurationManager Configuration { get; }
        public IWebHostEnvironment Environment { get; }
        
        public WebApplicationBuilder()
        {
            Services = new ServiceCollection();
            Configuration = new ConfigurationManager();
            Environment = new WebHostEnvironment();
        }

        public WebApplication Build()
        {
            return new WebApplication(Services, Configuration, Environment);
        }
    }

    public class WebApplication : IDisposable
    {
        private readonly IServiceCollection _services;
        private readonly ConfigurationManager _configuration;
        private readonly IWebHostEnvironment _environment;
        private readonly List<Endpoint> _endpoints = new List<Endpoint>();
        private readonly List<Middleware> _middleware = new List<Middleware>();
        
        public IServiceCollection Services => _services;
        public ConfigurationManager Configuration => _configuration;
        public IWebHostEnvironment Environment => _environment;
        
        public WebApplication(IServiceCollection services, ConfigurationManager configuration, IWebHostEnvironment environment)
        {
            _services = services;
            _configuration = configuration;
            _environment = environment;
        }

        public void MapGet(string pattern, Func<HttpContext, Task> handler)
        {
            _endpoints.Add(new Endpoint("GET", pattern, handler));
        }

        public void MapPost(string pattern, Func<HttpContext, Task> handler)
        {
            _endpoints.Add(new Endpoint("POST", pattern, handler));
        }

        public void MapPut(string pattern, Func<HttpContext, Task> handler)
        {
            _endpoints.Add(new Endpoint("PUT", pattern, handler));
        }

        public void MapDelete(string pattern, Func<HttpContext, Task> handler)
        {
            _endpoints.Add(new Endpoint("DELETE", pattern, handler));
        }

        public void MapControllers()
        {
            Console.WriteLine("Controllers mapped");
        }

        public void Use(Func<HttpContext, Func<Task>, Task> middleware)
        {
            _middleware.Add(new Middleware(middleware));
        }

        public void UseRouting()
        {
            Console.WriteLine("Routing enabled");
        }

        public void UseAuthorization()
        {
            Console.WriteLine("Authorization enabled");
        }

        public void UseAuthentication()
        {
            Console.WriteLine("Authentication enabled");
        }

        public void UseCors(string policyName = null)
        {
            Console.WriteLine($"CORS enabled{(policyName != null ? $": {policyName}" : "")}");
        }

        public void UseHttpsRedirection()
        {
            Console.WriteLine("HTTPS redirection enabled");
        }

        public void UseStaticFiles()
        {
            Console.WriteLine("Static files enabled");
        }

        public async Task RunAsync(string url = "http://localhost:5000")
        {
            Console.WriteLine($"ViperNet application started on {url}");
            Console.WriteLine($"Environment: {_environment.EnvironmentName}");
            Console.WriteLine($"Endpoints: {_endpoints.Count}");
            Console.WriteLine($"Middleware: {_middleware.Count}");
            
            // Simulate running
            await Task.Delay(100);
        }

        public void Run(string url = "http://localhost:5000")
        {
            RunAsync(url).Wait();
        }

        public void Dispose()
        {
            Console.WriteLine("Application disposed");
        }
    }

    // Create web application
    public static class WebApplicationFactory
    {
        public static WebApplicationBuilder CreateBuilder(string[] args = null)
        {
            return new WebApplicationBuilder();
        }

        public static WebApplication Create(string[] args = null)
        {
            var builder = CreateBuilder(args);
            return builder.Build();
        }
    }

    // Endpoint representation
    public class Endpoint
    {
        public string Method { get; }
        public string Pattern { get; }
        public Func<HttpContext, Task> Handler { get; }

        public Endpoint(string method, string pattern, Func<HttpContext, Task> handler)
        {
            Method = method;
            Pattern = pattern;
            Handler = handler;
        }
    }

    // Middleware representation
    public class Middleware
    {
        public Func<HttpContext, Func<Task>, Task> Handler { get; }

        public Middleware(Func<HttpContext, Func<Task>, Task> handler)
        {
            Handler = handler;
        }
    }

    // HTTP Context
    public class HttpContext
    {
        public HttpRequest Request { get; }
        public HttpResponse Response { get; }
        public IDictionary<object, object> Items { get; }
        public IServiceProvider RequestServices { get; set; }
        public System.Security.Claims.ClaimsPrincipal User { get; set; }

        public HttpContext()
        {
            Request = new HttpRequest();
            Response = new HttpResponse();
            Items = new Dictionary<object, object>();
        }
    }

    // HTTP Request
    public class HttpRequest
    {
        public string Method { get; set; } = "GET";
        public string Path { get; set; } = "/";
        public QueryString Query { get; set; } = new QueryString();
        public IHeaderDictionary Headers { get; } = new HeaderDictionary();
        public Stream Body { get; set; } = new MemoryStream();
        public string ContentType { get; set; }
        public long? ContentLength { get; set; }
    }

    // HTTP Response
    public class HttpResponse
    {
        public int StatusCode { get; set; } = 200;
        public IHeaderDictionary Headers { get; } = new HeaderDictionary();
        public Stream Body { get; set; } = new MemoryStream();
        public string ContentType { get; set; }

        public async Task WriteAsync(string text)
        {
            var bytes = System.Text.Encoding.UTF8.GetBytes(text);
            await Body.WriteAsync(bytes, 0, bytes.Length);
        }

        public async Task WriteAsJsonAsync<T>(T obj)
        {
            ContentType = "application/json";
            var json = JsonSerializer.Serialize(obj);
            await WriteAsync(json);
        }
    }

    // Query string
    public class QueryString
    {
        private readonly Dictionary<string, string> _values = new Dictionary<string, string>();

        public string this[string key]
        {
            get => _values.ContainsKey(key) ? _values[key] : null;
            set => _values[key] = value;
        }

        public bool ContainsKey(string key) => _values.ContainsKey(key);
    }

    // Header dictionary
    public interface IHeaderDictionary : IDictionary<string, string>
    {
    }

    public class HeaderDictionary : Dictionary<string, string>, IHeaderDictionary
    {
    }

    // Service collection
    public interface IServiceCollection : IList<ServiceDescriptor>
    {
    }

    public class ServiceCollection : List<ServiceDescriptor>, IServiceCollection
    {
    }

    // Service descriptor
    public class ServiceDescriptor
    {
        public Type ServiceType { get; }
        public Type ImplementationType { get; }
        public object ImplementationInstance { get; }
        public Func<IServiceProvider, object> ImplementationFactory { get; }
        public ServiceLifetime Lifetime { get; }

        public ServiceDescriptor(Type serviceType, Type implementationType, ServiceLifetime lifetime)
        {
            ServiceType = serviceType;
            ImplementationType = implementationType;
            Lifetime = lifetime;
        }

        public ServiceDescriptor(Type serviceType, object implementationInstance)
        {
            ServiceType = serviceType;
            ImplementationInstance = implementationInstance;
            Lifetime = ServiceLifetime.Singleton;
        }

        public ServiceDescriptor(Type serviceType, Func<IServiceProvider, object> implementationFactory, ServiceLifetime lifetime)
        {
            ServiceType = serviceType;
            ImplementationFactory = implementationFactory;
            Lifetime = lifetime;
        }
    }

    // Service lifetime
    public enum ServiceLifetime
    {
        Singleton,
        Scoped,
        Transient
    }

    // Extension methods for service collection
    public static class ServiceCollectionExtensions
    {
        public static IServiceCollection AddSingleton<TService, TImplementation>(this IServiceCollection services)
            where TService : class
            where TImplementation : class, TService
        {
            services.Add(new ServiceDescriptor(typeof(TService), typeof(TImplementation), ServiceLifetime.Singleton));
            return services;
        }

        public static IServiceCollection AddSingleton<TService>(this IServiceCollection services, TService implementationInstance)
            where TService : class
        {
            services.Add(new ServiceDescriptor(typeof(TService), implementationInstance));
            return services;
        }

        public static IServiceCollection AddScoped<TService, TImplementation>(this IServiceCollection services)
            where TService : class
            where TImplementation : class, TService
        {
            services.Add(new ServiceDescriptor(typeof(TService), typeof(TImplementation), ServiceLifetime.Scoped));
            return services;
        }

        public static IServiceCollection AddTransient<TService, TImplementation>(this IServiceCollection services)
            where TService : class
            where TImplementation : class, TService
        {
            services.Add(new ServiceDescriptor(typeof(TService), typeof(TImplementation), ServiceLifetime.Transient));
            return services;
        }

        public static IServiceCollection AddControllers(this IServiceCollection services)
        {
            Console.WriteLine("Controllers added to services");
            return services;
        }

        public static IServiceCollection AddCors(this IServiceCollection services, Action<CorsOptions> setupAction = null)
        {
            Console.WriteLine("CORS added to services");
            setupAction?.Invoke(new CorsOptions());
            return services;
        }
    }

    // CORS options
    public class CorsOptions
    {
        private readonly List<CorsPolicy> _policies = new List<CorsPolicy>();

        public void AddPolicy(string name, Action<CorsPolicyBuilder> configurePolicy)
        {
            var builder = new CorsPolicyBuilder();
            configurePolicy(builder);
            _policies.Add(builder.Build(name));
        }
    }

    public class CorsPolicy
    {
        public string Name { get; set; }
        public List<string> Origins { get; } = new List<string>();
        public List<string> Methods { get; } = new List<string>();
        public List<string> Headers { get; } = new List<string>();
    }

    public class CorsPolicyBuilder
    {
        private readonly CorsPolicy _policy = new CorsPolicy();

        public CorsPolicyBuilder WithOrigins(params string[] origins)
        {
            _policy.Origins.AddRange(origins);
            return this;
        }

        public CorsPolicyBuilder AllowAnyOrigin()
        {
            _policy.Origins.Add("*");
            return this;
        }

        public CorsPolicyBuilder AllowAnyMethod()
        {
            _policy.Methods.Add("*");
            return this;
        }

        public CorsPolicyBuilder AllowAnyHeader()
        {
            _policy.Headers.Add("*");
            return this;
        }

        public CorsPolicy Build(string name)
        {
            _policy.Name = name;
            return _policy;
        }
    }

    // Configuration
    public class ConfigurationManager
    {
        private readonly Dictionary<string, string> _values = new Dictionary<string, string>();

        public string this[string key]
        {
            get => _values.ContainsKey(key) ? _values[key] : null;
            set => _values[key] = value;
        }

        public string GetConnectionString(string name)
        {
            return this[$"ConnectionStrings:{name}"];
        }

        public T GetSection<T>(string key) where T : new()
        {
            return new T();
        }
    }

    // Web host environment
    public interface IWebHostEnvironment
    {
        string EnvironmentName { get; set; }
        string ApplicationName { get; set; }
        string ContentRootPath { get; set; }
        string WebRootPath { get; set; }
    }

    public class WebHostEnvironment : IWebHostEnvironment
    {
        public string EnvironmentName { get; set; } = "Development";
        public string ApplicationName { get; set; } = "ViperNet";
        public string ContentRootPath { get; set; } = Directory.GetCurrentDirectory();
        public string WebRootPath { get; set; } = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot");
    }

    // Controller base
    public abstract class ControllerBase
    {
        public HttpContext HttpContext { get; set; }
        
        public OkResult Ok() => new OkResult();
        public OkObjectResult Ok(object value) => new OkObjectResult(value);
        public BadRequestResult BadRequest() => new BadRequestResult();
        public BadRequestObjectResult BadRequest(object error) => new BadRequestObjectResult(error);
        public NotFoundResult NotFound() => new NotFoundResult();
        public NotFoundObjectResult NotFound(object value) => new NotFoundObjectResult(value);
        public CreatedResult Created(string uri, object value) => new CreatedResult(uri, value);
        public NoContentResult NoContent() => new NoContentResult();
    }

    // Action results
    public abstract class ActionResult
    {
        public abstract int StatusCode { get; }
    }

    public class OkResult : ActionResult
    {
        public override int StatusCode => 200;
    }

    public class OkObjectResult : ActionResult
    {
        public object Value { get; }
        public override int StatusCode => 200;
        
        public OkObjectResult(object value)
        {
            Value = value;
        }
    }

    public class BadRequestResult : ActionResult
    {
        public override int StatusCode => 400;
    }

    public class BadRequestObjectResult : ActionResult
    {
        public object Value { get; }
        public override int StatusCode => 400;
        
        public BadRequestObjectResult(object value)
        {
            Value = value;
        }
    }

    public class NotFoundResult : ActionResult
    {
        public override int StatusCode => 404;
    }

    public class NotFoundObjectResult : ActionResult
    {
        public object Value { get; }
        public override int StatusCode => 404;
        
        public NotFoundObjectResult(object value)
        {
            Value = value;
        }
    }

    public class CreatedResult : ActionResult
    {
        public string Uri { get; }
        public object Value { get; }
        public override int StatusCode => 201;
        
        public CreatedResult(string uri, object value)
        {
            Uri = uri;
            Value = value;
        }
    }

    public class NoContentResult : ActionResult
    {
        public override int StatusCode => 204;
    }

    // Attributes
    [AttributeUsage(AttributeTargets.Class)]
    public class ApiControllerAttribute : Attribute
    {
    }

    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
    public class RouteAttribute : Attribute
    {
        public string Template { get; }
        
        public RouteAttribute(string template)
        {
            Template = template;
        }
    }

    [AttributeUsage(AttributeTargets.Method)]
    public class HttpGetAttribute : Attribute
    {
        public string Template { get; }
        
        public HttpGetAttribute(string template = null)
        {
            Template = template;
        }
    }

    [AttributeUsage(AttributeTargets.Method)]
    public class HttpPostAttribute : Attribute
    {
        public string Template { get; }
        
        public HttpPostAttribute(string template = null)
        {
            Template = template;
        }
    }

    [AttributeUsage(AttributeTargets.Method)]
    public class HttpPutAttribute : Attribute
    {
        public string Template { get; }
        
        public HttpPutAttribute(string template = null)
        {
            Template = template;
        }
    }

    [AttributeUsage(AttributeTargets.Method)]
    public class HttpDeleteAttribute : Attribute
    {
        public string Template { get; }
        
        public HttpDeleteAttribute(string template = null)
        {
            Template = template;
        }
    }

    [AttributeUsage(AttributeTargets.Parameter)]
    public class FromBodyAttribute : Attribute
    {
    }

    [AttributeUsage(AttributeTargets.Parameter)]
    public class FromQueryAttribute : Attribute
    {
    }

    [AttributeUsage(AttributeTargets.Parameter)]
    public class FromRouteAttribute : Attribute
    {
    }

    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
    public class AuthorizeAttribute : Attribute
    {
        public string Policy { get; set; }
        public string Roles { get; set; }
    }
}
