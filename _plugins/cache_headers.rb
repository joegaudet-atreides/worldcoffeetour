# Override WEBrick to serve static assets with proper cache headers for development
Jekyll::Hooks.register :site, :post_write do |site|
  next unless Jekyll.env == "development"
  
  # Only run this if we're using WEBrick
  if defined?(WEBrick) && defined?(WEBrick::HTTPServlet::FileHandler)
    original_service = WEBrick::HTTPServlet::FileHandler.instance_method(:service)
    
    WEBrick::HTTPServlet::FileHandler.define_method(:service) do |req, res|
      original_service.bind(self).call(req, res)
      
      # Override cache headers for static assets
      if req.path_info =~ /\.(jpg|jpeg|png|gif|webp|svg|css|js|woff|woff2)$/i
        res['Cache-Control'] = 'public, max-age=86400' # 24 hours
        res['ETag'] = nil if res['ETag'] # Remove problematic ETag
      end
    end
  end
end