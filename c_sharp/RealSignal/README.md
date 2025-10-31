# SignalR Emulator - Real-time Communication

A lightweight emulation of **SignalR**, Microsoft's library for adding real-time web functionality to applications. SignalR enables server-side code to push content to connected clients instantly.

## Features

This emulator implements core SignalR functionality:

### Hubs
- **Hub Base Class**: Central class for real-time communication
- **Client-Server Communication**: Bidirectional messaging
- **Method Invocation**: Call client methods from server
- **Typed Hubs**: Strongly-typed hub interfaces
- **Connection Context**: Access connection information

### Connection Management
- **Connection Lifecycle**: Connect and disconnect events
- **Connection ID**: Unique identifier for each connection
- **User Identification**: Associate connections with users
- **Connection Tracking**: Monitor active connections
- **OnConnected/OnDisconnected**: Lifecycle hooks

### Group Management
- **Create Groups**: Organize connections into groups
- **Add to Group**: Add connections to groups
- **Remove from Group**: Remove connections from groups
- **Group Messaging**: Send messages to all group members
- **Multiple Groups**: Connection can be in multiple groups

### Client Communication
- **Broadcast to All**: Send to all connected clients
- **Target Specific Clients**: Send to specific connections
- **Group Messaging**: Send to group members
- **User Messaging**: Send to all user connections
- **Caller Communication**: Reply to calling client
- **Others Communication**: Send to all except caller

### Messaging Patterns
- **SendAsync**: Asynchronous message sending
- **Method Invocation**: Invoke client-side methods
- **Multiple Parameters**: Send complex data
- **Return Values**: Receive responses from clients

## What It Emulates

This tool emulates [ASP.NET Core SignalR](https://docs.microsoft.com/en-us/aspnet/core/signalr/), Microsoft's real-time communication library used in applications like chat systems, dashboards, gaming, and collaborative tools.

### Core Components Implemented

1. **Hub**
   - Base class for server-side hubs
   - Client method invocation
   - Connection management
   - Lifecycle events

2. **Clients**
   - All clients targeting
   - Specific client targeting
   - Group targeting
   - User targeting

3. **Groups**
   - Add/remove connections
   - Group messaging
   - Dynamic group membership

4. **Context**
   - Connection information
   - User identity
   - Request metadata

## Usage

### Define a Hub

```csharp
using SignalREmulator;

public class ChatHub : Hub
{
    // Send message to all clients
    public async Task SendMessage(string user, string message)
    {
        await Clients.All.SendAsync("ReceiveMessage", user, message);
    }
    
    // Send message to specific group
    public async Task SendMessageToGroup(string groupName, string user, string message)
    {
        await Clients.Group(groupName).SendAsync("ReceiveMessage", user, message);
    }
    
    // Send message to specific user
    public async Task SendMessageToUser(string userId, string message)
    {
        await Clients.User(userId).SendAsync("ReceiveMessage", message);
    }
    
    // Connection lifecycle
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
```

### Group Management

```csharp
public class ChatHub : Hub
{
    public async Task JoinGroup(string groupName)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, groupName);
        await Clients.Group(groupName).SendAsync("UserJoined", 
            Context.ConnectionId, groupName);
    }
    
    public async Task LeaveGroup(string groupName)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, groupName);
        await Clients.Group(groupName).SendAsync("UserLeft", 
            Context.ConnectionId, groupName);
    }
    
    public async Task SendToGroup(string groupName, string message)
    {
        await Clients.Group(groupName).SendAsync("ReceiveGroupMessage", 
            Context.ConnectionId, message);
    }
}
```

### Client Targeting

```csharp
public class NotificationHub : Hub
{
    // Send to all clients
    public async Task BroadcastNotification(string notification)
    {
        await Clients.All.SendAsync("ReceiveNotification", notification);
    }
    
    // Send to specific client
    public async Task SendToClient(string connectionId, string message)
    {
        await Clients.Client(connectionId).SendAsync("ReceiveMessage", message);
    }
    
    // Send to multiple clients
    public async Task SendToClients(List<string> connectionIds, string message)
    {
        await Clients.Clients(connectionIds).SendAsync("ReceiveMessage", message);
    }
    
    // Send to all except caller
    public async Task SendToOthers(string message)
    {
        await Clients.Others.SendAsync("ReceiveMessage", message);
    }
    
    // Reply to caller only
    public async Task Echo(string message)
    {
        await Clients.Caller.SendAsync("ReceiveEcho", message);
    }
}
```

### User-specific Messaging

```csharp
public class MessagingHub : Hub
{
    public async Task SendPrivateMessage(string targetUserId, string message)
    {
        await Clients.User(targetUserId).SendAsync("ReceivePrivateMessage",
            Context.UserIdentifier, message);
    }
    
    public async Task SendToMultipleUsers(List<string> userIds, string message)
    {
        await Clients.Users(userIds).SendAsync("ReceiveMessage", message);
    }
}
```

### Client Connection

```csharp
// Create connection
var connectionManager = new ConnectionManager();
var connection = connectionManager.AddConnection("unique-connection-id", "user-123");

// Register client-side handlers
connection.On("ReceiveMessage", async (args) => 
{
    var user = args[0] as string;
    var message = args[1] as string;
    Console.WriteLine($"{user}: {message}");
    return Task.CompletedTask;
});

connection.On("ReceiveNotification", async (args) =>
{
    var notification = args[0] as string;
    Console.WriteLine($"Notification: {notification}");
    return Task.CompletedTask;
});
```

### Complete Example - Chat Application

```csharp
using System;
using System.Threading.Tasks;
using SignalREmulator;

public class Program
{
    public static async Task Main()
    {
        // Create hub
        var chatHub = new ChatHub();
        var connectionManager = new ConnectionManager();
        
        // Create connections for users
        var alice = connectionManager.AddConnection("alice-conn", "alice");
        var bob = connectionManager.AddConnection("bob-conn", "bob");
        var charlie = connectionManager.AddConnection("charlie-conn", "charlie");
        
        // Register message handlers
        alice.On("ReceiveMessage", async (args) =>
        {
            Console.WriteLine($"Alice received: {args[0]} - {args[1]}");
            return Task.CompletedTask;
        });
        
        bob.On("ReceiveMessage", async (args) =>
        {
            Console.WriteLine($"Bob received: {args[0]} - {args[1]}");
            return Task.CompletedTask;
        });
        
        charlie.On("ReceiveMessage", async (args) =>
        {
            Console.WriteLine($"Charlie received: {args[0]} - {args[1]}");
            return Task.CompletedTask;
        });
        
        // Broadcast message to all
        await chatHub.SendMessage("Alice", "Hello everyone!");
        
        // Create a group
        chatHub.Context.ConnectionId = "alice-conn";
        await chatHub.JoinGroup("developers");
        
        chatHub.Context.ConnectionId = "bob-conn";
        await chatHub.JoinGroup("developers");
        
        // Send to group
        await chatHub.SendMessageToGroup("developers", "Bob", "Hi devs!");
        
        // Send to specific user
        await chatHub.SendMessageToUser("alice", "System", "Welcome!");
    }
}
```

## Testing

```bash
csc /out:test.exe SignalREmulator.cs TestSignalR.cs
./test.exe
```

Or create a .csproj file:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net6.0</TargetFramework>
  </PropertyGroup>
</Project>
```

Then run:
```bash
dotnet build
dotnet run
```

## Use Cases

1. **Chat Applications**: Real-time messaging systems
2. **Live Dashboards**: Real-time data visualization
3. **Notifications**: Push notifications to users
4. **Collaboration Tools**: Real-time document editing
5. **Gaming**: Multiplayer game state synchronization
6. **Monitoring**: Live system monitoring and alerts
7. **Social Features**: Real-time feeds and updates

## Key Differences from Real SignalR

1. **No WebSocket**: Doesn't use actual WebSocket connections
2. **In-Memory Only**: No persistent storage or backplane
3. **No Transports**: No fallback transports (Server-Sent Events, Long Polling)
4. **Simplified Protocol**: No MessagePack or JSON protocol
5. **No Hub Filters**: Hub pipeline not implemented
6. **No Authentication**: Authorization not built-in
7. **No Reconnection**: Automatic reconnection not included
8. **No Streaming**: Streaming methods not implemented
9. **Single Process**: No scale-out with Redis/Azure SignalR
10. **No Client Libraries**: No JavaScript/TypeScript client

## SignalR Concepts

### Hubs
Hubs are high-level pipelines that allow clients and servers to call methods on each other. SignalR handles the cross-machine dispatching automatically.

### Connections
Each client connection is represented by a unique connection ID. Connections can be organized into groups and associated with users.

### Groups
Groups provide a way to broadcast messages to subsets of connections. Connections can be dynamically added or removed from groups.

### Clients
The Clients property provides access to all connected clients, groups of clients, or specific clients to send messages to.

### Real-time Communication
SignalR enables real-time bidirectional communication between server and client, allowing servers to push content to connected clients instantly.

## Advanced Features (Not Implemented)

- **Streaming**: Server-to-client and client-to-server streaming
- **MessagePack Protocol**: Binary serialization for performance
- **Strong Typing**: Strongly-typed hub clients
- **Hub Filters**: Pipeline for cross-cutting concerns
- **Authorization**: Built-in authentication/authorization
- **Backplane**: Redis/Azure Service Bus for scale-out
- **Reconnection**: Automatic reconnection handling
- **Circuit Breaker**: Resilience patterns

## License

Educational emulator for learning purposes.

## References

- [SignalR Documentation](https://docs.microsoft.com/en-us/aspnet/core/signalr/)
- [SignalR Hubs](https://docs.microsoft.com/en-us/aspnet/core/signalr/hubs)
- [SignalR GitHub](https://github.com/dotnet/aspnetcore/tree/main/src/SignalR)
