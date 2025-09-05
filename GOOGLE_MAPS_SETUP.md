# Google Maps API Setup Guide

## Getting Your API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. **IMPORTANT: Enable these APIs:**
   - Go to "APIs & Services" → "Library"
   - Search and enable **Maps JavaScript API**
   - Search and enable **Places API**
4. Go to "APIs & Services" → "Credentials"
5. Click "Create Credentials" → "API Key"
6. Copy your API key

## Setting Up the API Key

1. Open `/admin.html` 
2. Find this line (around line 644):
   ```javascript
   <script async defer src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBwYF8fK0D6eHmJKiPW9L0DxVPz8FcYTxo&libraries=places&callback=initGoogleMaps"></script>
   ```
3. Replace `AIzaSyBwYF8fK0D6eHmJKiPW9L0DxVPz8FcYTxo` with your actual API key

## API Key Restrictions (Recommended)

1. In Google Cloud Console, click on your API key
2. Under "Application restrictions":
   - Select "HTTP referrers"
   - Add your domain: `yourdomain.com/*` and `localhost:*`
3. Under "API restrictions":
   - Select "Restrict key"
   - Select only: Places API, Maps JavaScript API

## Free Tier Limits

- **$200 free credit per month**
- Places Text Search: ~11,700 requests/month free
- Places Autocomplete: ~70,000 requests/month free

For an admin interface with occasional use, you should stay well within the free tier.

## Testing

1. Open the admin interface
2. Try searching for "Augusta Coffee Toronto" or any business
3. You should now see accurate results from Google Places

## Troubleshooting

If searches aren't working:
1. Check browser console for errors
2. Verify API key is correct
3. Ensure Places API is enabled in Google Cloud Console
4. Check API quotas haven't been exceeded