/**
 * FlareProx - Cloudflare Worker URL Redirection Script (ESM)
 * Original script by https://github.com/MrTurvey/flareprox/blob/main/flareprox.py
 */
export default {
    async fetch(request, env, ctx) {
        return handleRequest(request)
    }
}

async function handleRequest(request) {
    try {
        const url = new URL(request.url)
        const targetUrl = getTargetUrl(url, request.headers)

        if (!targetUrl) {
            return createErrorResponse('No target URL specified', {
                usage: {
                    query_param: '?url=https://example.com',
                    header: 'X-Target-URL: https://example.com',
                    path: '/https://example.com'
                }
            }, 400)
        }

        let targetURL
        try {
            targetURL = new URL(targetUrl)
        } catch (e) {
            return createErrorResponse('Invalid target URL', { provided: targetUrl }, 400)
        }

        // Build target URL with filtered query parameters
        const targetParams = new URLSearchParams()
        for (const [key, value] of url.searchParams) {
            if (!['url', '_cb', '_t'].includes(key)) {
                targetParams.append(key, value)
            }
        }
        if (targetParams.toString()) {
            targetURL.search = targetParams.toString()
        }

        // Create proxied request
        const proxyRequest = createProxyRequest(request, targetURL)
        const response = await fetch(proxyRequest)

        // Process and return response
        return createProxyResponse(response, request.method)

    } catch (error) {
        return createErrorResponse('Proxy request failed', {
            message: error.message,
            timestamp: new Date().toISOString()
        }, 500)
    }
}

function getTargetUrl(url, headers) {
    // Priority: query param > header > path
    let targetUrl = url.searchParams.get('url')

    if (!targetUrl) {
        targetUrl = headers.get('X-Target-URL')
    }

    if (!targetUrl && url.pathname !== '/') {
        const pathUrl = url.pathname.slice(1)
        if (pathUrl.startsWith('http')) {
            targetUrl = pathUrl
        }
    }

    return targetUrl
}

function createProxyRequest(request, targetURL) {
    const proxyHeaders = new Headers()
    const allowedHeaders = [
        'accept', 'accept-language', 'accept-encoding', 'authorization',
        'cache-control', 'content-type', 'origin', 'referer', 'user-agent'
    ]

    // Copy allowed headers
    for (const [key, value] of request.headers) {
        if (allowedHeaders.includes(key.toLowerCase())) {
            proxyHeaders.set(key, value)
        }
    }

    proxyHeaders.set('Host', targetURL.hostname)

    // Set X-Forwarded-For header
    const customXForwardedFor = request.headers.get('X-My-X-Forwarded-For')
    if (customXForwardedFor) {
        proxyHeaders.set('X-Forwarded-For', customXForwardedFor)
    } else {
        proxyHeaders.set('X-Forwarded-For', generateRandomIP())
    }

    return new Request(targetURL.toString(), {
        method: request.method,
        headers: proxyHeaders,
        body: ['GET', 'HEAD'].includes(request.method) ? null : request.body
    })
}

function createProxyResponse(response, requestMethod) {
    const responseHeaders = new Headers()

    // Copy response headers (excluding problematic ones)
    for (const [key, value] of response.headers) {
        if (!['content-encoding', 'content-length', 'transfer-encoding'].includes(key.toLowerCase())) {
            responseHeaders.set(key, value)
        }
    }

    // Add CORS headers
    responseHeaders.set('Access-Control-Allow-Origin', '*')
    responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD')
    responseHeaders.set('Access-Control-Allow-Headers', '*')

    if (requestMethod === 'OPTIONS') {
        return new Response(null, { status: 204, headers: responseHeaders })
    }

    return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders
    })
}

function createErrorResponse(error, details, status) {
    return new Response(JSON.stringify({ error, ...details }), {
        status,
        headers: { 'Content-Type': 'application/json' }
    })
}

function generateRandomIP() {
    return [1, 2, 3, 4].map(() => Math.floor(Math.random() * 255) + 1).join('.')
}
