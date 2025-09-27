export default {
	async fetch(request, env, ctx) {
	  if (request.method === "POST" && new URL(request.url).pathname === "/score-route") {
		try {
		  const body = await request.json();
  
		  // Use provided route_id OR generate one from points
		  let routeId = body.route_id;
		  if (!routeId) {
			const text = JSON.stringify(body.points);
			// Simple hash (FNV-1a like)
			let hash = 2166136261;
			for (let i = 0; i < text.length; i++) {
			  hash ^= text.charCodeAt(i);
			  hash = (hash * 16777619) >>> 0;
			}
			routeId = `auto-${hash}`;
		  }
  
		  const routeKey = `route:${routeId}`;
  
		  // 1. Try cache
		  const cached = await env.SAFEROUTE_CACHE.get(routeKey);
		  if (cached) {
			return new Response(cached, {
			  headers: { "Content-Type": "application/json", "X-Cache": "HIT" }
			});
		  }
  
		  // 2. Forward to backend
<<<<<<< HEAD
		  console.log("Forwarding to backend:", env.BACKEND_URL + "/score-route");
=======
>>>>>>> 552480c (Added Cloudflare cache using KV pairs to increase systems efficency and connect to the cloud)
		  const backendRes = await fetch(env.BACKEND_URL + "/score-route", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ ...body, route_id: routeId })
		  });
<<<<<<< HEAD

		  console.log("Backend response status:", backendRes.status);
		  const result = await backendRes.text();
		  console.log("Backend response:", result);
=======
  
		  const result = await backendRes.text();
>>>>>>> 552480c (Added Cloudflare cache using KV pairs to increase systems efficency and connect to the cloud)
  
		  // 3. Save to KV
		  await env.SAFEROUTE_CACHE.put(routeKey, result);
  
		  return new Response(result, {
			headers: { "Content-Type": "application/json", "X-Cache": "MISS" }
		  });
		} catch (err) {
		  return new Response(JSON.stringify({ error: err.message }), { status: 500 });
		}
	  }
  
	  // Default fallback
	  return new Response("SafeRoute Worker is live 🚦", {
		headers: { "Content-Type": "text/plain" }
	  });
	}
  };
  