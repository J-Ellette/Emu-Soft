# Ruby on Rails Emulator - Web Framework

A lightweight emulation of **Ruby on Rails**, the popular Ruby web application framework known for convention over configuration and rapid development.

## Features

This emulator implements core Rails functionality:

### ActiveRecord (ORM)
- **Model Definition**: Define database models
- **CRUD Operations**: Create, Read, Update, Delete
- **Finder Methods**: find, find_by, where, all, first, last, count
- **Validations**: validates_presence_of
- **Associations**: has_many, belongs_to
- **Callbacks**: Basic lifecycle callbacks
- **Query Interface**: Chainable query methods

### ActionController (MVC Controller)
- **Controller Base Class**: Base class for controllers
- **Request Handling**: HTTP request processing
- **Response Rendering**: render json, text, html
- **Redirects**: redirect_to
- **Before Actions**: before_action filters
- **Session Management**: Session storage
- **Parameters**: Request parameters

### ActionView (Views)
- **Template Rendering**: Render views and partials
- **View Helpers**: link_to, form_for
- **Form Builders**: text_field, submit
- **Partial Rendering**: Render partial templates

### Router (URL Routing)
- **RESTful Routes**: resources method
- **Custom Routes**: get, post, put, delete
- **Route Matching**: Path matching
- **Named Routes**: Route helpers

### ActiveSupport (Utilities)
- **Core Extensions**: String extensions
- **Hash with Indifferent Access**: Symbol/string key access
- **Time Helpers**: Date and time utilities
- **Inflections**: titleize, parameterize

## What It Emulates

This tool emulates [Ruby on Rails](https://rubyonrails.org/), one of the most popular web frameworks in the world, powering sites like GitHub, Shopify, Airbnb, and Basecamp.

### Core Components Implemented

1. **ActiveRecord**
   - ORM pattern
   - Database abstraction
   - Associations
   - Validations

2. **ActionController**
   - Request/Response cycle
   - Controller actions
   - Filters and callbacks

3. **ActionView**
   - Template rendering
   - View helpers
   - Partial rendering

4. **Router**
   - RESTful routing
   - Route definitions
   - URL generation

## Usage

### Define Models (ActiveRecord)

```ruby
require_relative 'rails_emulator'

class Post < ActiveRecord::Base
  validates_presence_of :title, :content
  belongs_to :author
  has_many :comments
end

class Author < ActiveRecord::Base
  validates_presence_of :name
  has_many :posts
end

class Comment < ActiveRecord::Base
  validates_presence_of :body
  belongs_to :post
end
```

### CRUD Operations

```ruby
# Create
post = Post.new(title: "Hello Rails", content: "My first post")
post.save

# Or use create
post = Post.create(title: "Hello Rails", content: "My first post")

# Read
post = Post.find(1)
posts = Post.all
tech_posts = Post.where(category: "tech")
first_post = Post.first
last_post = Post.last
count = Post.count

# Update
post.update(title: "Updated Title")
# or
post.title = "Updated Title"
post.save

# Delete
post.destroy
Post.destroy_all
```

### Validations

```ruby
class User < ActiveRecord::Base
  validates_presence_of :email, :password
end

user = User.new(email: "")
user.valid?  # => false
user.errors  # => ["email can't be blank", "password can't be blank"]

user.email = "user@example.com"
user.password = "secret"
user.valid?  # => true
user.save    # => true
```

### Associations

```ruby
# Define associations
class Blog < ActiveRecord::Base
  has_many :posts
end

class Post < ActiveRecord::Base
  belongs_to :blog
end

# Use associations
blog = Blog.create(name: "My Blog")
post = Post.create(title: "First Post", blog_id: blog.id)

# Access associated records
blog.posts  # => [post]
post.blog   # => blog
```

### Controllers

```ruby
class PostsController < ActionController::Base
  before_action :authenticate_user, only: [:create, :update, :destroy]
  
  def index
    posts = Post.all
    render json: posts
  end
  
  def show
    post = Post.find(params[:id])
    render json: post
  end
  
  def create
    post = Post.new(params[:post])
    if post.save
      render json: post, status: 201
    else
      render json: { errors: post.errors }, status: 422
    end
  end
  
  def update
    post = Post.find(params[:id])
    if post.update(params[:post])
      render json: post
    else
      render json: { errors: post.errors }, status: 422
    end
  end
  
  def destroy
    post = Post.find(params[:id])
    post.destroy
    head 204
  end
  
  private
  
  def authenticate_user
    # Authentication logic
  end
end
```

### Routing

```ruby
app = create_rails_app

app.routes do |router|
  # RESTful routes
  router.resources :posts
  router.resources :authors
  
  # Custom routes
  router.get '/about', to: 'pages#about'
  router.post '/contact', to: 'pages#contact'
  
  # Root route
  router.get '/', to: 'home#index'
end
```

### Views

```ruby
view = ActionView::Base.new

# Render partial
html = view.render(partial: 'post', locals: { post: post })

# Link helper
link = view.link_to('Home', '/')
# => "<a href='/'>Home</a>"

# Form helper
form = view.form_for(post) do
  view.text_field(:title)
end
```

### Complete Example

```ruby
require_relative 'rails_emulator'

# Define models
class Article < ActiveRecord::Base
  validates_presence_of :title, :body
  belongs_to :user
  has_many :tags
end

class User < ActiveRecord::Base
  validates_presence_of :email
  has_many :articles
end

# Create records
user = User.create(email: "author@example.com")
article = Article.create(
  title: "Rails Guide",
  body: "Learn Rails the easy way",
  user_id: user.id
)

# Query records
articles = Article.where(user_id: user.id)
article = Article.find_by(title: "Rails Guide")

# Update
article.update(title: "Complete Rails Guide")

# Associations
user_articles = user.articles
article_author = article.user

# Controller
class ArticlesController < ActionController::Base
  def index
    articles = Article.all
    render json: articles
  end
  
  def show
    article = Article.find(params[:id])
    render json: article
  end
end

# Routes
app = create_rails_app
app.routes do |router|
  router.resources :articles
  router.get '/', to: 'home#index'
end

app.start
```

## Testing

```bash
ruby test_rails_emulator.rb
```

## Use Cases

1. **Learning Rails**: Understand Rails concepts without installation
2. **Development**: Rapid prototyping
3. **Testing**: Test Rails patterns
4. **Education**: Teaching web development
5. **Documentation**: Demonstrate Rails features
6. **API Design**: Design RESTful APIs

## Key Differences from Real Rails

1. **No Database**: Doesn't connect to actual databases
2. **In-Memory Storage**: Data stored in memory only
3. **Simplified Routing**: Basic route matching
4. **No Asset Pipeline**: Asset compilation not included
5. **Limited Validations**: Only basic validations
6. **No Migrations**: Database migrations not implemented
7. **Simplified Views**: Template rendering is basic
8. **No Mailers**: Email functionality not included
9. **No Background Jobs**: No ActiveJob support
10. **No WebSocket**: ActionCable not included

## Rails Concepts

### Convention Over Configuration
Rails follows conventions to minimize configuration. For example, a `Post` model automatically maps to a `posts` table.

### MVC Pattern
Rails uses Model-View-Controller architecture:
- **Model**: Data and business logic (ActiveRecord)
- **View**: Presentation layer (ActionView)
- **Controller**: Request handling (ActionController)

### RESTful Design
Rails encourages RESTful resource routing with standard CRUD actions:
- GET /posts (index)
- GET /posts/:id (show)
- POST /posts (create)
- PUT /posts/:id (update)
- DELETE /posts/:id (destroy)

### Active Record Pattern
Models inherit from ActiveRecord::Base and represent database tables. Each instance represents a row.

## License

Educational emulator for learning purposes.

## References

- [Ruby on Rails Documentation](https://guides.rubyonrails.org/)
- [Rails API](https://api.rubyonrails.org/)
- [Rails GitHub](https://github.com/rails/rails)
