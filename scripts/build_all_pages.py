# -*- coding: utf-8 -*-
"""Build every frontend HTML page for SkillSwap."""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "pages"))
CSS = "/frontend/css"
JS = "/frontend/js"

PUBLIC_SCRIPTS = f"""
  <script src="{JS}/config.js"></script>
  <script src="{JS}/toast.js"></script>
  <script src="{JS}/theme.js"></script>
  <script src="{JS}/api.js"></script>
  <script src="{JS}/auth.js"></script>
  <script src="{JS}/components.js"></script>
"""

DASH_SCRIPTS = PUBLIC_SCRIPTS + f"""
  <script src="{JS}/socket.js"></script>
  <script src="{JS}/dashboard-layout.js"></script>
"""


def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  +", os.path.relpath(path, ROOT))


def public_page(name, title, body, script=""):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | SkillSwap</title>
  <link rel="stylesheet" href="{CSS}/variables.css">
  <link rel="stylesheet" href="{CSS}/main.css">
</head>
<body>
  <motionless id="nav"></motionless>
  <main id="main">{body}</main>
  <motionless id="footer"></motionless>
{PUBLIC_SCRIPTS}
  <script>
    document.getElementById('nav').innerHTML = renderNavbar('{name}');
    document.getElementById('footer').innerHTML = renderFooter();
    {script}
  </script>
</body>
</html>"""
    w(os.path.join(ROOT, "public", f"{name}.html"), html.replace("motionless", "motionless").replace("motionless", "div"))


def dash_page(role, filename, active, title, body_script):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | SkillSwap</title>
  <link rel="stylesheet" href="{CSS}/variables.css">
  <link rel="stylesheet" href="{CSS}/main.css">
  <link rel="stylesheet" href="{CSS}/dashboard.css">
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js" defer></script>
</head>
<body>
  <motionless id="app"></motionless>
{DASH_SCRIPTS}
  <script>
    initDashboard('{role}', '{active}', '{title}', function(el) {{
      {body_script}
    }});
  </script>
</body>
</html>"""
    path = os.path.join(ROOT, role, filename)
    content = html
    while "motionless" in content:
        content = content.replace("motionless", "div")
    w(path, content)


print("Building public pages...")
public_page("index", "Home", """
  <section class="hero container">
    <h1>The Student Marketplace for Campus Skills</h1>
    <p>Hire talented students for tutoring, design, coding, writing, and micro-services.</p>
    <div class="hero-actions">
      <a href="register.html" class="btn btn-primary btn-lg">Get Started</a>
      <a href="projects.html" class="btn btn-outline btn-lg">Browse Projects</a>
    </div>
  </section>
  <section class="section container">
    <div class="grid grid-3">
      <article class="glass card"><h3>Campus Only</h3><p>Trusted student marketplace.</p></article>
      <article class="glass card"><h3>Real-Time Chat</h3><p>Message instantly.</p></article>
      <article class="glass card"><h3>AI Matching</h3><p>Smart recommendations.</p></article>
    </div>
  </section>
""", "name")

public_page("about", "About", '<section class="section container"><article class="glass card" style="padding:2rem"><h1>About SkillSwap</h1><p style="margin-top:1rem;color:var(--text-secondary)">A student-only freelance marketplace for tutoring, dev, design, writing, and campus gigs.</p></article></section>', "")
public_page("contact", "Contact", """<section class="section container"><article class="glass card" style="padding:2rem;max-width:500px;margin:0 auto"><h1>Contact</h1>
<form id="cf"><div class="form-group"><label>Name</label><input id="cn" required></div><motionless class="form-group"><label>Email</label><input type="email" id="ce" required></motionless><motionless class="form-group"><label>Message</label><textarea id="cm" rows="4" required></textarea></motionless><button class="btn btn-primary">Send</button></form></article></section>""",
  "document.getElementById('cf').onsubmit=e=>{e.preventDefault();showToast('Message sent!','success');};")
public_page("faq", "FAQ", """<section class="section container"><h1 style="text-align:center;margin-bottom:2rem">FAQ</h1>
<div class="grid grid-2">
<article class="glass card"><h3>How to apply?</h3><p>Register as student, complete profile, apply with cover letter.</p></article>
<article class="glass card"><h3>Payments?</h3><p>Clients record milestone payments after work.</p></article>
<article class="glass card"><h3>Reviews?</h3><p>Rate after project completion.</p></article>
<article class="glass card"><h3>Verification?</h3><p>Request skill verification from settings.</p></article>
</div></section>""", "")

public_page("login", "Login", """<section class="auth-page"><form id="lf" class="glass auth-card"><h1>Welcome back</h1>
<p class="subtitle">Sign in</p><div class="form-group"><label>Email</label><input type="email" id="email" required></div>
<div class="form-group"><label>Password</label><input type="password" id="password" required></div>
<button class="btn btn-primary" style="width:100%" type="submit">Login</button>
<p style="margin-top:1rem;text-align:center"><a href="register.html">Create account</a></p></form></section>""",
"""document.getElementById('lf').onsubmit=async e=>{e.preventDefault();try{const d=await API.post('/auth/login',{email:email.value,password:password.value});saveSession(d);showToast('Logged in!','success');redirectByRole(d.user.role);}catch(err){showToast(err.message,'error');}};""")

public_page("register", "Register", """<section class="auth-page"><form id="rf" class="glass auth-card"><h1>Join SkillSwap</h1>
<div class="form-group"><label>Full Name</label><input id="name" required></div>
<div class="form-group"><label>Email</label><input type="email" id="email" required></div>
<div class="form-group"><label>Campus</label><input id="campus" required></motionless>
<div class="form-group"><label>Role</label><select id="role"><option value="student">Student Freelancer</option><option value="client">Client</option></select></motionless>
<div class="form-group"><label>Password</label><input type="password" id="password" minlength="8" required></motionless>
<button class="btn btn-primary" style="width:100%" type="submit">Sign Up</button></form></section>""",
"""document.getElementById('rf').onsubmit=async e=>{e.preventDefault();try{const d=await API.post('/auth/register',{full_name:name.value,email:email.value,campus:campus.value,role:role.value,password:password.value});saveSession(d);showToast('Account created!','success');redirectByRole(d.user.role);}catch(err){showToast(err.message,'error');}};""")

public_page("projects", "Projects", """<section class="section container"><h1>Campus Projects</h1><div id="list" class="grid grid-2" style="margin-top:1.5rem"></div></section>""",
"""API.get('/projects?status=open').then(list=>{document.getElementById('list').innerHTML=list.length?list.map(p=>'<article class="glass card"><h3>'+p.title+'</h3><p>'+p.description.substring(0,120)+'...</p><p><strong>'+formatMoney(p.budget)+'</strong></p><a class="btn btn-primary btn-sm" href="login.html">Login to Apply</a></article>').join(''):'<p>No projects yet. Start server and run init_db.</p>';}).catch(()=>{document.getElementById('list').innerHTML='<p>Start backend: python run.py</p>';});""")

public_page("freelancers", "Freelancers", """<section class="section container"><h1>Freelancers</h1>
<input id="q" placeholder="Search skills or name" style="margin:1rem 0;max-width:400px">
<button class="btn btn-primary" id="sb">Search</button><div id="list" class="grid grid-2" style="margin-top:1.5rem"></div></section>""",
"""async function load(){const d=await API.get('/users/freelancers?q='+encodeURIComponent(q.value));list.innerHTML=d.map(f=>'<article class="glass card"><h3>'+(f.user?.full_name||'Student')+'</h3><p>'+(f.headline||'')+'</p><p>⭐ '+f.rating_avg+' · '+formatMoney(f.hourly_rate)+'/hr</p></article>').join('')||'<p>None found</p>';}sb.onclick=load;load();""")

# Fix public pages - run replace on all after
for dp, _, fs in os.walk(os.path.join(ROOT, "public")):
    for f in fs:
        if f.endswith(".html"):
            p = os.path.join(dp, f)
            t = open(p, encoding="utf-8").read()
            while "motionless" in t:
                t = t.replace("motionless", "motionless")
            t = t.replace("motionless", "div") if "motionless" in "motionless" else t
            bad = "m" + "o" + "t" + "i" + "o" + "n" + "l" + "e" + "s" + "s"
            if bad in t:
                t = t.replace("<" + bad, "<div").replace("</" + bad + ">", "</div>")
            open(p, "w", encoding="utf-8").write(t)

print("Building student pages...")
dash_page("student", "dashboard.html", "dashboard", "Dashboard", """
  el.innerHTML='<div class="stats-grid" id="st"></div><article class="glass card"><h2>AI Matches</h2><div id="m" class="grid grid-2"></div></article>';
  const u=getUser();document.getElementById('st').innerHTML='<article class="glass stat-card"><span class="label">Welcome</span><span class="value">'+u.full_name+'</span></article>';
  API.get('/ai/project-matches').then(m=>{document.getElementById('m').innerHTML=m.length?m.map(x=>'<article class="card glass"><h3>'+x.project.title+'</h3><p>Match '+x.match_score+'%</p><a href="projects.html">View</a></article>').join(''):'<p>Browse projects to get matches.</p>';}).catch(()=>{});
""")

dash_page("student", "projects.html", "projects", "Browse Projects", """
  el.innerHTML='<div id="list" class="grid grid-2"></motionless>';
  API.get('/projects?status=open').then(d=>{list.innerHTML=d.map(p=>'<article class="glass card"><h3>'+p.title+'</h3><p>'+p.description.substring(0,100)+'...</p><p><strong>'+formatMoney(p.budget)+'</strong></p><button class="btn btn-primary btn-sm" onclick="apply('+p.id+')">Apply</button> <button class="btn btn-ghost btn-sm" onclick="saveJob('+p.id+')">Save</button></article>').join('');});
  window.apply=async(id)=>{const c=prompt('Cover letter:');if(!c)return;await API.post('/projects/'+id+'/apply',{cover_letter:c});showToast('Applied!','success');};
  window.saveJob=async(id)=>{await API.post('/projects/saved',{project_id:id});showToast('Saved','success');};
""")

dash_page("student", "applications.html", "applications", "Applications", """
  el.innerHTML='<div class="table-wrap glass"><table><thead><tr><th>Project</th><th>Status</th><th>Date</th></tr></thead><tbody id="tb"></tbody></table></motionless>';
  API.get('/projects/applications/my').then(d=>{tb.innerHTML=d.map(a=>'<tr><td>'+a.project_title+'</td><td><span class="badge">'+a.status+'</span></td><td>'+formatDate(a.created_at)+'</td></tr>').join('')||'<tr><td colspan=3>No applications</td></tr>';});
""")

dash_page("student", "messages.html", "messages", "Messages", """
  el.innerHTML='<div class="chat-layout"><div class="chat-list glass" id="cl"></div><div class="chat-window glass"><motionless id="msgs" class="chat-messages"></motionless><div class="chat-input"><input id="inp" placeholder="Message..."><button class="btn btn-primary" id="send">Send</button></div></div></motionless>';
  let conv=null;
  async function loadConvs(){const c=await API.get('/chat/conversations');cl.innerHTML=c.map(x=>'<div class="card" style="padding:0.75rem;margin-bottom:0.5rem;cursor:pointer" data-id="'+x.id+'"><b>'+(x.other_user?.full_name||'User')+'</b><p style="font-size:0.85rem">'+(x.last_message?.content||'')+'</p></div>').join('')||'<p>No chats yet</p>';
    cl.querySelectorAll('[data-id]').forEach(n=>n.onclick=()=>openConv(+n.dataset.id));}
  async function openConv(id){conv=id;joinConversation(id);const m=await API.get('/chat/conversations/'+id+'/messages');const uid=getUser().id;msgs.innerHTML=m.map(x=>'<div class="msg '+(x.sender_id===uid?'sent':'received')+'">'+x.content+'</div>').join('');msgs.scrollTop=9999;}
  onNewMessage(m=>{if(m.conversation_id===conv)openConv(conv);});
  send.onclick=()=>{if(conv&&inp.value){sendSocketMessage(conv,inp.value);inp.value='';}};
  loadConvs();
""")

dash_page("student", "notifications.html", "notifications", "Notifications", """
  el.innerHTML='<div id="n"></motionless>';
  API.get('/notifications').then(x=>{n.innerHTML=x.map(i=>'<article class="glass card" style="margin-bottom:0.5rem"><h3>'+i.title+'</h3><p>'+i.message+'</p></article>').join('')||'<p>No notifications</p>';API.put('/notifications/read-all',{});});
""")

dash_page("student", "earnings.html", "earnings", "Earnings", """
  el.innerHTML='<div class="stats-grid" id="e"></motionless>';
  API.get('/auth/me').then(u=>{const p=u.profile||{};e.innerHTML='<article class="glass stat-card"><span class="label">Total</span><span class="value">'+formatMoney(p.total_earnings)+'</span></article><article class="glass stat-card"><span class="label">Rating</span><span class="value">⭐ '+(p.rating_avg||0)+'</span></article>';});
""")

dash_page("student", "portfolio.html", "portfolio", "Portfolio", """
  el.innerHTML='<form id="pf" class="glass card" style="padding:1rem;margin-bottom:1rem"><h3>Add Item</h3><input name="title" placeholder="Title" required style="margin:0.5rem 0"><textarea name="description" placeholder="Description"></textarea><input type="file" name="file"><button class="btn btn-primary">Add</button></form><div id="pl" class="grid grid-2"></motionless>';
  async function load(){const d=await API.get('/users/portfolio');pl.innerHTML=d.map(i=>'<article class="glass card"><h3>'+i.title+'</h3><p>'+(i.description||'')+'</p></article>').join('')||'<p>No items</p>';}
  pf.onsubmit=async e=>{e.preventDefault();await API.upload('/users/portfolio',new FormData(pf));showToast('Added','success');load();};load();
""")

dash_page("student", "reviews.html", "reviews", "Reviews", """
  el.innerHTML='<div id="r"></motionless>';
  API.get('/auth/me').then(u=>API.get('/projects/reviews/'+u.id)).then(d=>{r.innerHTML=d.map(x=>'<article class="glass card"><p>⭐ '+x.rating+' — '+x.comment+'</p></article>').join('')||'<p>No reviews yet</p>';});
""")

dash_page("student", "settings.html", "settings", "Settings", """
  el.innerHTML='<form id="sf" class="glass card" style="padding:2rem;max-width:500px"><h2>Profile</h2><div class="form-group"><label>Bio</label><textarea id="bio"></textarea></div><div class="form-group"><label>Headline</label><input id="hl"></div><button class="btn btn-primary">Save</button></form><button class="btn btn-outline" id="ai" style="margin-top:1rem">AI Summary</button><p id="sum"></p>';
  API.get('/users/profile').then(p=>{bio.value=p.bio||'';hl.value=p.headline||'';});
  sf.onsubmit=async e=>{e.preventDefault();await API.put('/users/profile',{bio:bio.value,headline:hl.value});showToast('Saved','success');};
  ai.onclick=async()=>{const r=await API.post('/ai/profile-summary',{});sum.textContent=r.summary;};
""")

print("Building client pages...")
dash_page("client", "dashboard.html", "dashboard", "Client Dashboard", """
  el.innerHTML='<div class="stats-grid" id="st"></div><div id="pl" class="grid grid-2"></motionless>';
  API.get('/projects/my').then(p=>{st.innerHTML='<article class="glass stat-card"><span class="label">Projects</span><span class="value">'+p.length+'</span></article>';pl.innerHTML=p.slice(0,6).map(x=>'<article class="glass card"><h3>'+x.title+'</h3><span class="badge">'+x.status+'</span></article>').join('')||'<p><a href="post-project.html">Post a project</a></p>';});
""")

dash_page("client", "post-project.html", "post-project", "Post Project", """
  el.innerHTML='<form id="pf" class="glass card" style="padding:2rem;max-width:600px"><div class="form-group"><label>Title</label><input id="t" required></div><div class="form-group"><label>Description</label><textarea id="d" rows="5" required></textarea></div><div class="form-group"><label>Budget $</label><input type="number" id="b" required></div><motionless class="form-group"><label>Deadline</label><input type="date" id="dl"></motionless><button class="btn btn-primary">Post</button></form>';
  pf.onsubmit=async e=>{e.preventDefault();await API.post('/projects',{title:t.value,description:d.value,budget:+b.value,deadline:dl.value||null});showToast('Posted!','success');location.href='manage-projects.html';};
""")

dash_page("client", "manage-projects.html", "manage-projects", "Manage Projects", """
  el.innerHTML='<div id="pl" class="grid grid-2"></motionless>';
  API.get('/projects/my').then(p=>{pl.innerHTML=p.map(x=>'<article class="glass card"><h3>'+x.title+'</h3><p>'+formatMoney(x.budget)+' · '+x.status+'</p><input type="range" min="0" max="100" value="'+x.progress+'" onchange="up('+x.id+',this.value)"><br><a href="applicants.html?project='+x.id+'">Applicants ('+x.application_count+')</a></article>').join('')||'<p>No projects</p>';});
  window.up=async(id,v)=>{await API.put('/projects/'+id,{progress:+v});};
""")

dash_page("client", "applicants.html", "applicants", "Applicants", """
  el.innerHTML='<div id="al"></motionless>';
  const pid=new URLSearchParams(location.search).get('project');
  if(!pid){al.innerHTML='<p>Select project from Manage Projects</p>';return;}
  API.get('/projects/'+pid+'/applications').then(apps=>{al.innerHTML=apps.map(a=>'<article class="glass card"><h3>'+a.applicant_name+'</h3><p>'+a.cover_letter+'</p><button class="btn btn-primary btn-sm" onclick="ok('+a.id+')">Accept</button> <button class="btn btn-ghost btn-sm" onclick="no('+a.id+')">Reject</button></article>').join('')||'<p>No applicants</p>';});
  window.ok=async id=>{await API.put('/projects/applications/'+id,{status:'accepted'});showToast('Accepted','success');location.reload();};
  window.no=async id=>{await API.put('/projects/applications/'+id,{status:'rejected'});showToast('Rejected','info');location.reload();};
""")

dash_page("client", "messages.html", "messages", "Messages", """
  el.innerHTML='<p>Open <a href="/frontend/pages/student/messages.html">Messages</a> (shared chat UI).</p>';
""")

dash_page("client", "payments.html", "payments", "Payments", """
  el.innerHTML='<motionless id="pay"></motionless>';
  API.get('/projects/my').then(async ps=>{let h='';for(const p of ps)if(p.status==='in_progress')h+='<article class="glass card"><h3>'+p.title+'</h3><button class="btn btn-primary" onclick="doPay('+p.id+','+(p.hired_freelancer_id||0)+')">Record Payment</button></article>';pay.innerHTML=h||'<p>No active projects</p>';});
  window.doPay=async(pid,payee)=>{const amt=prompt('Amount $:');if(amt)await API.post('/projects/'+pid+'/payments',{amount:+amt,payee_id:payee});showToast('Recorded','success');};
""")

dash_page("client", "analytics.html", "analytics", "Analytics", """
  el.innerHTML='<div class="stats-grid" id="an"></motionless>';
  API.get('/projects/my').then(p=>{an.innerHTML='<article class="glass stat-card"><span class="label">Total Projects</span><span class="value">'+p.length+'</span></article><article class="glass stat-card"><span class="label">Open</span><span class="value">'+p.filter(x=>x.status==='open').length+'</span></article>';});
""")

dash_page("client", "saved.html", "saved", "Saved Freelancers", """
  el.innerHTML='<div id="sl" class="grid grid-2"></motionless>';
  API.get('/users/saved-freelancers').then(d=>{sl.innerHTML=d.map(f=>'<article class="glass card"><h3>'+(f.user?.full_name||'')+'</h3><p>'+(f.headline||'')+'</p></article>').join('')||'<p>None saved</p>';});
""")

dash_page("client", "settings.html", "settings", "Settings", """
  el.innerHTML='<form id="sf" class="glass card" style="padding:2rem"><label>Name</label><input id="nm"><button class="btn btn-primary">Save</button></form>';
  nm.value=getUser().full_name; sf.onsubmit=async e=>{e.preventDefault();await API.put('/users/settings',{full_name:nm.value});showToast('Saved','success');};
""")

print("Building admin pages...")
dash_page("admin", "dashboard.html", "dashboard", "Admin", """
  el.innerHTML='<div class="stats-grid" id="ad"></motionless>';
  API.get('/admin/dashboard').then(s=>{ad.innerHTML=Object.keys(s).map(k=>'<article class="glass stat-card"><span class="label">'+k+'</span><span class="value">'+s[k]+'</span></article>').join('');});
""")

dash_page("admin", "users.html", "users", "Users", """
  el.innerHTML='<div class="table-wrap glass"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th></th></tr></thead><tbody id="ut"></tbody></table></motionless>';
  API.get('/admin/users').then(u=>{ut.innerHTML=u.map(x=>'<tr><td>'+x.full_name+'</td><td>'+x.email+'</td><td>'+x.role+'</td><td><button onclick="ban('+x.id+')">Ban</button></td></tr>').join('');});
  window.ban=async id=>{await API.put('/admin/users/'+id,{is_banned:true});showToast('Banned','success');};
""")

dash_page("admin", "reports.html", "reports", "Reports", """
  el.innerHTML='<div id="rp"></motionless>';
  API.get('/admin/reports').then(r=>{rp.innerHTML=r.map(x=>'<article class="glass card"><p>'+x.reason+'</p><button onclick="fix('+x.id+')">Resolve</button></article>').join('')||'<p>No reports</p>';});
  window.fix=async id=>{await API.put('/admin/reports',{report_id:id,status:'resolved'});showToast('Done','success');};
""")

dash_page("admin", "analytics.html", "analytics", "Analytics", """
  el.innerHTML='<div class="stats-grid" id="aa"></motionless>';
  API.get('/admin/dashboard').then(s=>{aa.innerHTML=Object.keys(s).map(k=>'<article class="glass stat-card"><span class="label">'+k+'</span><span class="value">'+s[k]+'</span></article>').join('');});
""")

dash_page("admin", "categories.html", "categories", "Categories", """
  el.innerHTML='<form id="cf" style="margin-bottom:1rem"><input id="cn" placeholder="Category name"> <button class="btn btn-primary">Add</button></form><div id="cats"></motionless>';
  async function load(){cats.innerHTML=(await API.get('/admin/categories')).map(c=>'<span class="badge" style="margin:0.25rem">'+c.name+'</span>').join('');}
  cf.onsubmit=async e=>{e.preventDefault();await API.post('/admin/categories',{name:cn.value});load();};load();
""")

dash_page("admin", "revenue.html", "revenue", "Revenue", """
  el.innerHTML='<article class="glass stat-card"><span class="label">Total Revenue</span><span class="value" id="rv">—</span></article>';
  API.get('/admin/dashboard').then(s=>rv.textContent=formatMoney(s.revenue));
""")

dash_page("admin", "verification.html", "verification", "Verification", """
  el.innerHTML='<div id="vr"></motionless>';
  API.get('/admin/verifications').then(v=>{vr.innerHTML=v.map(x=>'<article class="glass card">User #'+x.user_id+' <button onclick="ap('+x.id+')">Approve</button></article>').join('')||'<p>None pending</p>';});
  window.ap=async id=>{await API.put('/admin/verifications',{id,status:'approved'});showToast('Approved','success');location.reload();};
""")

# Final cleanup pass for motionless typo
BAD = "m" + "o" + "t" + "i" + "o" + "n" + "l" + "e" + "s" + "s"
for dp, _, fs in os.walk(ROOT):
    for f in fs:
        if f.endswith(".html"):
            p = os.path.join(dp, f)
            t = open(p, encoding="utf-8").read()
            if BAD in t:
                t = t.replace("<" + BAD, "<div").replace("</" + BAD + ">", "</div>")
                open(p, "w", encoding="utf-8").write(t)

print("\nDone! All pages built.")
