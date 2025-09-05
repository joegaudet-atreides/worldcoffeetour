#!/usr/bin/env ruby
require 'webrick'
require 'jekyll'

# Build Jekyll site first
puts "Building Jekyll site..."
Jekyll::Commands::Build.process({})

# Configure WEBrick with better caching for development
server = WEBrick::HTTPServer.new(
  :Port => 4001,
  :DocumentRoot => '_site',
  :DirectoryIndex => ['index.html']
)

# Add custom headers for static assets
server.mount_proc '/' do |req, res|
  file_path = File.join('_site', req.path_info)
  
  # Check if it's a static asset
  if req.path_info =~ /\.(jpg|jpeg|png|gif|webp|svg|css|js|woff|woff2)$/i
    if File.exist?(file_path)
      # Set proper cache headers
      res['Cache-Control'] = 'public, max-age=86400' # 24 hours
      res['ETag'] = nil
      
      # Serve the file
      res.body = File.read(file_path)
      res['Content-Type'] = WEBrick::HTTPUtils.mime_type(req.path_info, WEBrick::HTTPUtils::DefaultMimeTypes)
    else
      res.status = 404
    end
  else
    # For non-assets, serve normally
    WEBrick::HTTPServlet::FileHandler.new(server, '_site').service(req, res)
  end
end

trap('INT') { server.shutdown }

puts "Starting server with image caching on http://localhost:4001"
puts "Images will be cached for 24 hours in browser cache"
server.start