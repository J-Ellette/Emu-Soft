#!/usr/bin/env ruby
require_relative 'GemTracks'

puts "=== Rails Emulator Tests ===\n\n"

# Test ActiveRecord
puts "--- Test: ActiveRecord CRUD ---"

class User < ActiveRecord::Base
  validates_presence_of :email
  has_many :posts
end

class Post < ActiveRecord::Base
  validates_presence_of :title
  belongs_to :user
end

# Create
user1 = User.create(email: "alice@example.com")
user2 = User.create(email: "bob@example.com")

post1 = Post.create(title: "First Post", content: "Hello World", user_id: user1.id)
post2 = Post.create(title: "Second Post", content: "Rails is great", user_id: user1.id)

puts "Created #{User.count} users and #{Post.count} posts"

# Read
found_user = User.find(1)
puts "Found user: #{found_user.attributes[:email]}"

all_posts = Post.all
puts "Total posts: #{all_posts.length}"

# Update
post1.update(title: "Updated First Post")
puts "Updated post title"

# Delete
post2.destroy
puts "Deleted post, remaining: #{Post.count}"

puts

# Test Validations
puts "--- Test: Validations ---"

invalid_user = User.new
puts "Valid: #{invalid_user.valid?}"
puts "Errors: #{invalid_user.errors.join(', ')}"

valid_user = User.new(email: "valid@example.com")
puts "Valid: #{valid_user.valid?}"

puts

# Test Associations
puts "--- Test: Associations ---"

user_posts = user1.posts
puts "User 1 has #{user_posts.length} posts"

post_user = post1.user
puts "Post belongs to: #{post_user.attributes[:email]}"

puts

# Test Controller
puts "--- Test: ActionController ---"

class ArticlesController < ActionController::Base
  def index
    render json: { articles: ['Article 1', 'Article 2'] }
  end
  
  def show
    render json: { id: params[:id], title: 'Article' }
  end
  
  def redirect_home
    redirect_to '/'
  end
end

controller = ArticlesController.new
controller.params = { id: 1 }

controller.index
controller.show
controller.redirect_home

puts

# Test Router
puts "--- Test: Router ---"

app = create_rails_app

app.routes do |router|
  router.resources :posts
  router.resources :users
  router.get '/', to: 'home#index'
  router.get '/about', to: 'pages#about'
end

puts

# Test ActiveSupport
puts "--- Test: ActiveSupport ---"

title = "hello world"
puts "Original: #{title}"
puts "Titleized: #{title.titleize}"
puts "Parameterized: #{title.parameterize}"

puts

# Test View Helpers
puts "--- Test: ActionView ---"

view = ActionView::Base.new

link = view.link_to('Home', '/')
puts "Link: #{link}"

partial = view.render(partial: 'posts/post')
puts "Partial: #{partial[0..50]}..."

puts

puts "=== All Tests Completed Successfully ==="
