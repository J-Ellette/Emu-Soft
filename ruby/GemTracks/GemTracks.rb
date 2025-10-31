#!/usr/bin/env ruby
# Rails Framework Emulator
# Emulates core Ruby on Rails web framework functionality

require 'json'

# ActiveRecord - ORM Pattern
module ActiveRecord
  class Base
    @@table_name = nil
    @@columns = []
    @@records = []
    
    attr_accessor :id, :attributes
    
    def initialize(attributes = {})
      @attributes = attributes
      @id = attributes[:id]
      @new_record = true
      @errors = []
    end
    
    def self.table_name=(name)
      @@table_name = name
    end
    
    def self.table_name
      @@table_name || self.name.downcase + 's'
    end
    
    # Find methods
    def self.find(id)
      @@records.find { |r| r.id == id }
    end
    
    def self.find_by(conditions)
      @@records.find do |record|
        conditions.all? { |key, value| record.attributes[key] == value }
      end
    end
    
    def self.where(conditions)
      @@records.select do |record|
        conditions.all? { |key, value| record.attributes[key] == value }
      end
    end
    
    def self.all
      @@records
    end
    
    def self.first
      @@records.first
    end
    
    def self.last
      @@records.last
    end
    
    def self.count
      @@records.length
    end
    
    # CRUD operations
    def save
      if valid?
        if @new_record
          @id = (@@records.map(&:id).max || 0) + 1
          @attributes[:id] = @id
          @@records << self
          @new_record = false
          puts "[ActiveRecord] INSERT INTO #{self.class.table_name} #{@attributes.inspect}"
        else
          puts "[ActiveRecord] UPDATE #{self.class.table_name} SET #{@attributes.inspect} WHERE id=#{@id}"
        end
        true
      else
        false
      end
    end
    
    def save!
      raise "Validation failed" unless save
    end
    
    def update(attributes)
      @attributes.merge!(attributes)
      save
    end
    
    def destroy
      @@records.delete(self)
      puts "[ActiveRecord] DELETE FROM #{self.class.table_name} WHERE id=#{@id}"
      true
    end
    
    def self.create(attributes)
      record = new(attributes)
      record.save
      record
    end
    
    def self.destroy_all
      count = @@records.length
      @@records.clear
      puts "[ActiveRecord] DELETE FROM #{table_name}"
      count
    end
    
    # Validations
    def self.validates_presence_of(*attrs)
      @required_attrs ||= []
      @required_attrs.concat(attrs)
    end
    
    def valid?
      @errors.clear
      if self.class.instance_variable_get(:@required_attrs)
        self.class.instance_variable_get(:@required_attrs).each do |attr|
          if @attributes[attr].nil? || @attributes[attr].to_s.strip.empty?
            @errors << "#{attr} can't be blank"
          end
        end
      end
      @errors.empty?
    end
    
    def errors
      @errors
    end
    
    # Associations
    def self.has_many(association)
      define_method(association) do
        association_class = association.to_s.capitalize.chop
        Object.const_get(association_class).where(
          "#{self.class.name.downcase}_id".to_sym => @id
        )
      end
    end
    
    def self.belongs_to(association)
      define_method(association) do
        association_class = association.to_s.capitalize
        foreign_key = "#{association}_id".to_sym
        Object.const_get(association_class).find(@attributes[foreign_key])
      end
    end
  end
end

# ActionController - MVC Controller
module ActionController
  class Base
    attr_accessor :params, :request, :response, :session
    
    def initialize
      @params = {}
      @request = Request.new
      @response = Response.new
      @session = {}
      @before_actions = []
    end
    
    def self.before_action(method_name, options = {})
      @before_actions ||= []
      @before_actions << { method: method_name, options: options }
    end
    
    def render(options)
      if options[:json]
        @response.body = options[:json].to_json
        @response.content_type = 'application/json'
      elsif options[:text]
        @response.body = options[:text]
        @response.content_type = 'text/plain'
      elsif options[:html]
        @response.body = options[:html]
        @response.content_type = 'text/html'
      end
      
      @response.status = options[:status] || 200
      puts "[ActionController] Rendering #{@response.content_type} (Status: #{@response.status})"
    end
    
    def redirect_to(location)
      @response.status = 302
      @response.headers['Location'] = location
      puts "[ActionController] Redirect to #{location}"
    end
    
    def head(status)
      @response.status = status
      @response.body = nil
      puts "[ActionController] Returning head with status #{status}"
    end
  end
  
  class Request
    attr_accessor :method, :path, :headers, :body
    
    def initialize
      @method = 'GET'
      @path = '/'
      @headers = {}
      @body = ''
    end
    
    def get?
      @method == 'GET'
    end
    
    def post?
      @method == 'POST'
    end
    
    def put?
      @method == 'PUT'
    end
    
    def delete?
      @method == 'DELETE'
    end
  end
  
  class Response
    attr_accessor :status, :body, :headers, :content_type
    
    def initialize
      @status = 200
      @body = ''
      @headers = {}
      @content_type = 'text/html'
    end
  end
end

# ActionView - View Layer
module ActionView
  class Base
    def initialize(assigns = {})
      @assigns = assigns
    end
    
    def render(partial:, locals: {})
      puts "[ActionView] Rendering partial: #{partial}"
      "<div>Partial: #{partial}</div>"
    end
    
    def link_to(text, url, options = {})
      "<a href='#{url}'>#{text}</a>"
    end
    
    def form_for(object, &block)
      "<form>#{yield if block_given?}</form>"
    end
    
    def text_field(attribute)
      "<input type='text' name='#{attribute}' />"
    end
  end
end

# ActiveSupport - Utility Functions
module ActiveSupport
  class HashWithIndifferentAccess < Hash
    def [](key)
      super(key.to_s) || super(key.to_sym)
    end
  end
  
  module CoreExtensions
    module String
      def titleize
        self.split.map(&:capitalize).join(' ')
      end
      
      def parameterize
        self.downcase.gsub(/[^a-z0-9]+/, '-')
      end
    end
  end
end

String.include(ActiveSupport::CoreExtensions::String)

# Router - URL Routing
class Router
  def initialize
    @routes = []
  end
  
  def get(path, to:)
    @routes << { method: 'GET', path: path, to: to }
    puts "[Router] GET #{path} => #{to}"
  end
  
  def post(path, to:)
    @routes << { method: 'POST', path: path, to: to }
    puts "[Router] POST #{path} => #{to}"
  end
  
  def put(path, to:)
    @routes << { method: 'PUT', path: path, to: to }
    puts "[Router] PUT #{path} => #{to}"
  end
  
  def delete(path, to:)
    @routes << { method: 'DELETE', path: path, to: to }
    puts "[Router] DELETE #{path} => #{to}"
  end
  
  def resources(resource)
    puts "[Router] Resources for #{resource}"
    get "/#{resource}", to: "#{resource}#index"
    get "/#{resource}/new", to: "#{resource}#new"
    post "/#{resource}", to: "#{resource}#create"
    get "/#{resource}/:id", to: "#{resource}#show"
    get "/#{resource}/:id/edit", to: "#{resource}#edit"
    put "/#{resource}/:id", to: "#{resource}#update"
    delete "/#{resource}/:id", to: "#{resource}#destroy"
  end
  
  def match(method, path)
    @routes.find { |r| r[:method] == method && r[:path] == path }
  end
end

# Rails Application
class RailsApplication
  attr_accessor :router
  
  def initialize
    @router = Router.new
    @config = {}
  end
  
  def configure
    yield @config if block_given?
  end
  
  def routes
    yield @router if block_given?
  end
  
  def start
    puts "[Rails] Application started"
  end
end

# Helper to create Rails app
def create_rails_app
  RailsApplication.new
end
