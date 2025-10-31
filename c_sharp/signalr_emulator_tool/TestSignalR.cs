using System;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace SignalREmulator.Tests
{
    public class TestSignalR
    {
        public static async Task Main(string[] args)
        {
            Console.WriteLine("=== SignalR Emulator Tests ===\n");

            await TestBasicMessaging();
            await TestGroupMessaging();
            await TestUserMessaging();
            await TestConnectionLifecycle();
            await TestMultipleConnections();

            Console.WriteLine("\n=== All Tests Completed ===");
        }

        private static async Task TestBasicMessaging()
        {
            Console.WriteLine("Test 1: Basic Messaging");
            Console.WriteLine("------------------------");

            var hub = new ChatHub();
            var messagesReceived = new List<string>();

            // Set up message handler
            hub.Context.ConnectionId = "test-connection-1";

            await hub.SendMessage("Alice", "Hello World!");
            Console.WriteLine("✓ Sent message to all clients");

            Console.WriteLine();
        }

        private static async Task TestGroupMessaging()
        {
            Console.WriteLine("Test 2: Group Messaging");
            Console.WriteLine("------------------------");

            var hub = new ChatHub();
            var connectionManager = new ConnectionManager();

            // Create connections
            var conn1 = connectionManager.AddConnection("conn-1");
            var conn2 = connectionManager.AddConnection("conn-2");
            var conn3 = connectionManager.AddConnection("conn-3");

            var groupMessages = new List<string>();

            conn1.On("ReceiveMessage", async args =>
            {
                groupMessages.Add($"conn-1 received: {args[0]} - {args[1]}");
                await Task.CompletedTask;
            });

            conn2.On("ReceiveMessage", async args =>
            {
                groupMessages.Add($"conn-2 received: {args[0]} - {args[1]}");
                await Task.CompletedTask;
            });

            // Add connections to group
            hub.Context.ConnectionId = "conn-1";
            await hub.JoinGroup("developers");

            hub.Context.ConnectionId = "conn-2";
            await hub.JoinGroup("developers");

            // Send message to group
            await hub.SendMessageToGroup("developers", "Bob", "Group message!");

            Console.WriteLine("✓ Created group 'developers'");
            Console.WriteLine("✓ Added 2 connections to group");
            Console.WriteLine("✓ Sent message to group");

            Console.WriteLine();
        }

        private static async Task TestUserMessaging()
        {
            Console.WriteLine("Test 3: User-specific Messaging");
            Console.WriteLine("--------------------------------");

            var hub = new ChatHub();
            var connectionManager = new ConnectionManager();

            // Create user connections
            var aliceConn = connectionManager.AddConnection("alice-conn-1", "alice");
            var bobConn = connectionManager.AddConnection("bob-conn-1", "bob");

            var userMessages = new List<string>();

            aliceConn.On("ReceiveMessage", async args =>
            {
                userMessages.Add($"Alice received: {args[0]} - {args[1]}");
                await Task.CompletedTask;
            });

            bobConn.On("ReceiveMessage", async args =>
            {
                userMessages.Add($"Bob received: {args[0]} - {args[1]}");
                await Task.CompletedTask;
            });

            // Send message to specific user
            await hub.SendMessageToUser("alice", "System", "Welcome Alice!");

            Console.WriteLine("✓ Created user-specific connections");
            Console.WriteLine("✓ Sent message to specific user");

            Console.WriteLine();
        }

        private static async Task TestConnectionLifecycle()
        {
            Console.WriteLine("Test 4: Connection Lifecycle");
            Console.WriteLine("-----------------------------");

            var hub = new ChatHub();
            var connectionManager = new ConnectionManager();

            // Simulate connection
            var conn = connectionManager.AddConnection("lifecycle-conn-1");
            hub.Context.ConnectionId = "lifecycle-conn-1";

            await hub.OnConnectedAsync();
            Console.WriteLine("✓ Connection established");

            // Join a group
            await hub.JoinGroup("test-group");
            Console.WriteLine("✓ Joined group");

            // Leave the group
            await hub.LeaveGroup("test-group");
            Console.WriteLine("✓ Left group");

            // Simulate disconnection
            await hub.OnDisconnectedAsync(null);
            connectionManager.RemoveConnection("lifecycle-conn-1");
            Console.WriteLine("✓ Connection closed");

            Console.WriteLine();
        }

        private static async Task TestMultipleConnections()
        {
            Console.WriteLine("Test 5: Multiple Connections");
            Console.WriteLine("-----------------------------");

            var hub = new ChatHub();
            var connectionManager = new ConnectionManager();

            // Create multiple connections
            var connections = new List<HubConnection>();
            for (int i = 1; i <= 5; i++)
            {
                var conn = connectionManager.AddConnection($"multi-conn-{i}", $"user-{i}");
                connections.Add(conn);

                conn.On("ReceiveMessage", async args =>
                {
                    Console.WriteLine($"  Connection {conn.ConnectionId} received message");
                    await Task.CompletedTask;
                });
            }

            Console.WriteLine($"✓ Created 5 connections");

            // Broadcast to all
            await hub.SendMessage("Admin", "Broadcast message!");
            Console.WriteLine("✓ Broadcast message sent");

            // Send to specific clients
            var targetIds = new[] { "multi-conn-1", "multi-conn-3", "multi-conn-5" };
            await hub.Clients.Clients(targetIds).SendAsync("ReceiveMessage", "Admin", "Targeted message!");
            Console.WriteLine("✓ Sent message to specific clients");

            Console.WriteLine();
        }
    }
}
