using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SignalREmulator
{
    // Hub base class - core of SignalR
    public abstract class Hub
    {
        public IHubCallerContext Context { get; set; }
        public IHubClients Clients { get; set; }
        public IGroupManager Groups { get; set; }

        protected Hub()
        {
            Context = new HubCallerContext();
            Clients = new HubClients();
            Groups = new GroupManager();
        }

        public virtual Task OnConnectedAsync()
        {
            return Task.CompletedTask;
        }

        public virtual Task OnDisconnectedAsync(Exception exception)
        {
            return Task.CompletedTask;
        }
    }

    // Hub context interface
    public interface IHubCallerContext
    {
        string ConnectionId { get; set; }
        string UserIdentifier { get; set; }
        Dictionary<string, object> Items { get; }
    }

    // Hub caller context implementation
    public class HubCallerContext : IHubCallerContext
    {
        public string ConnectionId { get; set; }
        public string UserIdentifier { get; set; }
        public Dictionary<string, object> Items { get; }

        public HubCallerContext()
        {
            ConnectionId = Guid.NewGuid().ToString();
            Items = new Dictionary<string, object>();
        }
    }

    // Hub clients interface
    public interface IHubClients
    {
        IClientProxy All { get; }
        IClientProxy Caller { get; }
        IClientProxy Others { get; }
        IClientProxy Client(string connectionId);
        IClientProxy Clients(IEnumerable<string> connectionIds);
        IClientProxy Group(string groupName);
        IClientProxy Groups(IEnumerable<string> groupNames);
        IClientProxy User(string userId);
        IClientProxy Users(IEnumerable<string> userIds);
        IClientProxy AllExcept(params string[] excludedConnectionIds);
    }

    // Hub clients implementation
    public class HubClients : IHubClients
    {
        private readonly ConnectionManager _connectionManager = new ConnectionManager();

        public IClientProxy All => new ClientProxy(_connectionManager.GetAllConnections());
        public IClientProxy Caller => new ClientProxy(new List<HubConnection>());
        public IClientProxy Others => new ClientProxy(_connectionManager.GetAllConnections());

        public IClientProxy Client(string connectionId)
        {
            var connection = _connectionManager.GetConnection(connectionId);
            return new ClientProxy(connection != null ? new List<HubConnection> { connection } : new List<HubConnection>());
        }

        public IClientProxy Clients(IEnumerable<string> connectionIds)
        {
            var connections = connectionIds.Select(id => _connectionManager.GetConnection(id))
                .Where(c => c != null).ToList();
            return new ClientProxy(connections);
        }

        public IClientProxy Group(string groupName)
        {
            var connections = _connectionManager.GetGroupConnections(groupName);
            return new ClientProxy(connections);
        }

        public IClientProxy Groups(IEnumerable<string> groupNames)
        {
            var connections = groupNames.SelectMany(g => _connectionManager.GetGroupConnections(g))
                .Distinct().ToList();
            return new ClientProxy(connections);
        }

        public IClientProxy User(string userId)
        {
            var connections = _connectionManager.GetUserConnections(userId);
            return new ClientProxy(connections);
        }

        public IClientProxy Users(IEnumerable<string> userIds)
        {
            var connections = userIds.SelectMany(u => _connectionManager.GetUserConnections(u))
                .Distinct().ToList();
            return new ClientProxy(connections);
        }

        public IClientProxy AllExcept(params string[] excludedConnectionIds)
        {
            var connections = _connectionManager.GetAllConnections()
                .Where(c => !excludedConnectionIds.Contains(c.ConnectionId)).ToList();
            return new ClientProxy(connections);
        }
    }

    // Client proxy interface
    public interface IClientProxy
    {
        Task SendAsync(string method, params object[] args);
    }

    // Client proxy implementation
    public class ClientProxy : IClientProxy
    {
        private readonly List<HubConnection> _connections;

        public ClientProxy(List<HubConnection> connections)
        {
            _connections = connections;
        }

        public async Task SendAsync(string method, params object[] args)
        {
            foreach (var connection in _connections)
            {
                await connection.InvokeAsync(method, args);
            }
        }
    }

    // Group manager interface
    public interface IGroupManager
    {
        Task AddToGroupAsync(string connectionId, string groupName);
        Task RemoveFromGroupAsync(string connectionId, string groupName);
    }

    // Group manager implementation
    public class GroupManager : IGroupManager
    {
        private readonly ConnectionManager _connectionManager = new ConnectionManager();

        public Task AddToGroupAsync(string connectionId, string groupName)
        {
            _connectionManager.AddToGroup(connectionId, groupName);
            return Task.CompletedTask;
        }

        public Task RemoveFromGroupAsync(string connectionId, string groupName)
        {
            _connectionManager.RemoveFromGroup(connectionId, groupName);
            return Task.CompletedTask;
        }
    }

    // Hub connection
    public class HubConnection
    {
        public string ConnectionId { get; set; }
        public string UserId { get; set; }
        public List<string> Groups { get; set; }
        public Dictionary<string, Func<object[], Task>> Handlers { get; set; }

        public HubConnection(string connectionId)
        {
            ConnectionId = connectionId;
            Groups = new List<string>();
            Handlers = new Dictionary<string, Func<object[], Task>>();
        }

        public Task InvokeAsync(string method, object[] args)
        {
            if (Handlers.ContainsKey(method))
            {
                return Handlers[method](args);
            }
            return Task.CompletedTask;
        }

        public void On(string method, Func<object[], Task> handler)
        {
            Handlers[method] = handler;
        }
    }

    // Connection manager
    public class ConnectionManager
    {
        private static readonly Dictionary<string, HubConnection> _connections = new Dictionary<string, HubConnection>();
        private static readonly Dictionary<string, List<string>> _groups = new Dictionary<string, List<string>>();
        private static readonly Dictionary<string, List<string>> _users = new Dictionary<string, List<string>>();

        public HubConnection AddConnection(string connectionId, string userId = null)
        {
            var connection = new HubConnection(connectionId) { UserId = userId };
            _connections[connectionId] = connection;

            if (!string.IsNullOrEmpty(userId))
            {
                if (!_users.ContainsKey(userId))
                    _users[userId] = new List<string>();
                _users[userId].Add(connectionId);
            }

            return connection;
        }

        public void RemoveConnection(string connectionId)
        {
            if (_connections.TryGetValue(connectionId, out var connection))
            {
                // Remove from groups
                foreach (var group in connection.Groups.ToList())
                {
                    RemoveFromGroup(connectionId, group);
                }

                // Remove from users
                if (!string.IsNullOrEmpty(connection.UserId) && _users.ContainsKey(connection.UserId))
                {
                    _users[connection.UserId].Remove(connectionId);
                    if (_users[connection.UserId].Count == 0)
                        _users.Remove(connection.UserId);
                }

                _connections.Remove(connectionId);
            }
        }

        public HubConnection GetConnection(string connectionId)
        {
            return _connections.TryGetValue(connectionId, out var connection) ? connection : null;
        }

        public List<HubConnection> GetAllConnections()
        {
            return _connections.Values.ToList();
        }

        public void AddToGroup(string connectionId, string groupName)
        {
            if (_connections.TryGetValue(connectionId, out var connection))
            {
                if (!_groups.ContainsKey(groupName))
                    _groups[groupName] = new List<string>();

                if (!_groups[groupName].Contains(connectionId))
                {
                    _groups[groupName].Add(connectionId);
                    connection.Groups.Add(groupName);
                }
            }
        }

        public void RemoveFromGroup(string connectionId, string groupName)
        {
            if (_groups.ContainsKey(groupName))
            {
                _groups[groupName].Remove(connectionId);
                if (_groups[groupName].Count == 0)
                    _groups.Remove(groupName);
            }

            if (_connections.TryGetValue(connectionId, out var connection))
            {
                connection.Groups.Remove(groupName);
            }
        }

        public List<HubConnection> GetGroupConnections(string groupName)
        {
            if (_groups.TryGetValue(groupName, out var connectionIds))
            {
                return connectionIds.Select(id => GetConnection(id)).Where(c => c != null).ToList();
            }
            return new List<HubConnection>();
        }

        public List<HubConnection> GetUserConnections(string userId)
        {
            if (_users.TryGetValue(userId, out var connectionIds))
            {
                return connectionIds.Select(id => GetConnection(id)).Where(c => c != null).ToList();
            }
            return new List<HubConnection>();
        }
    }

    // Hub connection builder
    public class HubConnectionBuilder
    {
        private string _url;

        public HubConnectionBuilder WithUrl(string url)
        {
            _url = url;
            return this;
        }

        public HubConnection Build()
        {
            var connectionId = Guid.NewGuid().ToString();
            var connectionManager = new ConnectionManager();
            return connectionManager.AddConnection(connectionId);
        }
    }

    // Example chat hub
    public class ChatHub : Hub
    {
        public async Task SendMessage(string user, string message)
        {
            await Clients.All.SendAsync("ReceiveMessage", user, message);
        }

        public async Task SendMessageToGroup(string groupName, string user, string message)
        {
            await Clients.Group(groupName).SendAsync("ReceiveMessage", user, message);
        }

        public async Task SendMessageToUser(string userId, string user, string message)
        {
            await Clients.User(userId).SendAsync("ReceiveMessage", user, message);
        }

        public async Task JoinGroup(string groupName)
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, groupName);
            await Clients.Group(groupName).SendAsync("UserJoined", Context.ConnectionId, groupName);
        }

        public async Task LeaveGroup(string groupName)
        {
            await Groups.RemoveFromGroupAsync(Context.ConnectionId, groupName);
            await Clients.Group(groupName).SendAsync("UserLeft", Context.ConnectionId, groupName);
        }

        public override async Task OnConnectedAsync()
        {
            await Clients.All.SendAsync("UserConnected", Context.ConnectionId);
            await base.OnConnectedAsync();
        }

        public override async Task OnDisconnectedAsync(Exception exception)
        {
            await Clients.All.SendAsync("UserDisconnected", Context.ConnectionId);
            await base.OnDisconnectedAsync(exception);
        }
    }
}
