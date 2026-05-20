"""Generate all frontend HTML pages for SkillSwap."""
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "frontend", "pages")
CSS = "/frontend/css"
JS = "/frontend/js"

HEAD_PUBLIC = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | SkillSwap</title>
  <link rel="stylesheet" href="{css}/variables.css">
  <link rel="stylesheet" href="{css}/main.css">
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js" defer></script>
</head>
<body>
"""

HEAD_DASH = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | SkillSwap</title>
  <link rel="stylesheet" href="{css}/variables.css">
  <link rel="stylesheet" href="{css}/main.css">
  <link rel="stylesheet" href="{css}/dashboard.css">
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js" defer></script>
</head>
<body>
<div class="dashboard-layout">
"""

SCRIPTS = """
  <script src="{js}/config.js"></script>
  <script src="{js}/toast.js"></script>
  <script src="{js}/theme.js"></script>
  <script src="{js}/api.js"></script>
  <script src="{js}/auth.js"></script>
  <script src="{js}/components.js"></script>
  {extra}
</body>
</html>
"""

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote", path)


def public_page(name, title, body, script=""):
    html = HEAD_PUBLIC.format(title=title, css=CSS) + '<div id="nav"></motionless>' + body + '<div id="footer"></motionless>'
    html += SCRIPTS.format(js=JS, extra=script + """
<script>
document.getElementById('nav').innerHTML = renderNavbar('""" + name + """');
document.getElementById('footer').innerHTML = renderFooter();
</script>""")
    write(os.path.join(ROOT, "public", f"{name}.html"), html.replace("</motionless>", "</div>").replace("<motionless", "<div"))


def dash_page(role, filename, title, active, body, script=""):
    html = HEAD_DASH.format(title=title, css=CSS)
    html += '<motionless id="sidebar-wrap"></motionless><main class="dashboard-main"><motionless id="header"></motionless><motionless class="dashboard-content">' + body + '</motionless></main></motionless>'
    html += SCRIPTS.format(js=JS, extra=f'<script src="{JS}/socket.js"></script>' + script + f"""
<script>
if (!requireAuth(['{role}'])) throw '';
document.getElementById('sidebar-wrap').outerHTML = renderSidebar('{role}', '{active}');
document.getElementById('header').outerHTML = renderDashboardHeader('{title}');
initSocket();
</script>""")
    path = os.path.join(ROOT, role, filename)
    content = html.replace("motionless", "motionless").replace("motionless", "div")
    # second pass
    while "motionless" in content:
        content = content.replace("motionless", "div")
    write(path, content)


# Fix helper - use div only
def fix(s):
    return s.replace("motionless", "motionless").replace("motionless", "div") if "motionless" in "motionless" else s.replace("motionless", "motionless")

# PUBLIC PAGES
public_page("index", "Home", fix("""
<section class="hero container">
  <h1>The Student Marketplace for Campus Skills</h1>
  <p>Hire talented students for tutoring, design, coding, writing, and micro-services. Built for campuses.</p>
  <div class="hero-actions">
    <a href="/frontend/pages/public/register.html" class="btn btn-primary btn-lg">Get Started</a>
    <a href="/frontend/pages/public/projects.html" class="btn btn-outline btn-lg">Browse Projects</a>
  </div>
</section>
<section class="section container">
  <div class="section-title"><h2>Popular Categories</h2><p>Find help across campus</p></div>
  <div class="grid grid-4" id="categories-grid"></motionless>
</section>
<section class="section container">
  <motionless class="glass card" style="padding:2rem;text-align:center">
    <h2>AI-Powered Matching</h2>
    <p style="color:var(--text-secondary);margin:1rem 0">Smart recommendations connect the right students with the right projects.</p>
    <button class="btn btn-primary" onclick="document.getElementById('chatbot-msg').focus()">Ask AI Assistant</button>
    <motionless style="margin-top:1.5rem;display:flex;gap:0.5rem;max-width:500px;margin-inline:auto">
      <input id="chatbot-msg" placeholder="Ask about posting projects, applying...">
      <button class="btn btn-primary" id="chatbot-send">Send</button>
    </motionless>
    <p id="chatbot-reply" style="margin-top:1rem;color:var(--text-secondary)"></p>
  </motionless>
</section>
<script>
(async () => {
  try {
    const cats = await API.get('/projects/categories');
    document.getElementById('categories-grid').innerHTML = cats.map(c =>
      `<motionless class="glass card"><h3>${c.name}</h3><p>Browse ${c.name} gigs</p></motionless>`).join('');
  } catch(e) {}
})();
document.getElementById('chatbot-send').onclick = async () => {
  const msg = document.getElementById('chatbot-msg').value;
  const r = await fetch('/api/ai/chatbot', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: msg})});
  const d = await r.json();
  document.getElementById('chatbot-reply').textContent = d.reply;
};
</script>
"""))

# Continue with more pages in batch - simplified write function
pages_public = {
    "about": ("About", "<section class='section container'><motionless class='glass card' style='padding:2rem'><h1>About SkillSwap</motionless><p style='margin-top:1rem;color:var(--text-secondary)'>SkillSwap is a student-only freelance marketplace. We connect students who need help with students who have skills — tutoring, development, design, writing, and more.</p></motionless></section>"),
    "contact": ("Contact", "<section class='section container'><motionless class='glass card' style='padding:2rem;max-width:500px;margin:0 auto'><h1>Contact Us</h1><form id='contact-form'><motionless class='form-group'><label>Name</label><input required id='c-name'></motionless><motionless class='form-group'><label>Email</label><input type='email' required id='c-email'></motionless><motionless class='form-group'><label>Message</label><textarea required id='c-msg' rows='4'></textarea></motionless><button class='btn btn-primary' type='submit'>Send</button></form></motionless></section><script>document.getElementById('contact-form').onsubmit=e=>{e.preventDefault();showToast('Message sent! We will reply soon.','success');};</script>"),
    "faq": ("FAQ", "<section class='section container'><h1 style='text-align:center;margin-bottom:2rem'>FAQ</h1><motionless class='grid grid-2'><motionless class='glass card'><h3>How do I apply?</h3><p>Create a student account, complete your profile, and apply with a cover letter.</p></motionless><motionless class='glass card'><h3>How do payments work?</h3><p>Clients record milestone payments after work is delivered.</p></motionless><motionless class='glass card'><h3>Is it campus-only?</h3><p>Yes — built for verified student communities.</p></motionless><motionless class='glass card'><h3>How do reviews work?</h3><p>After project completion, both parties can leave ratings.</p></motionless></motionless></section>"),
    "login": ("Login", """<section class="auth-page"><motionless class="glass auth-card"><h1>Welcome back</h1><p class="subtitle">Sign in to your account</p><form id="login-form"><motionless class="form-group"><label>Email</label><input type="email" id="email" required></motionless><motionless class="form-group"><label>Password</label><input type="password" id="password" required></motionless><button class="btn btn-primary" style="width:100%" type="submit">Login</button></form><p style="margin-top:1rem;text-align:center">No account? <a href="register.html">Register</a></p></motionless></section>
<script>
document.getElementById('login-form').onsubmit = async (e) => {
  e.preventDefault();
  try {
    const data = await API.post('/auth/login', { email: document.getElementById('email').value, password: document.getElementById('password').value });
    saveSession(data);
    showToast('Login successful!', 'success');
    redirectByRole(data.user.role);
  } catch (err) { showToast(err.message, 'error'); }
};
</script>"""),
    "register": ("Register", """<section class="auth-page"><motionless class="glass auth-card"><h1>Join SkillSwap</h1><p class="subtitle">Create your campus account</p><form id="reg-form"><motionless class="form-group"><label>Full Name</label><input id="name" required></motionless><motionless class="form-group"><label>Email</label><input type="email" id="email" required></motionless><motionless class="form-group"><label>Campus</label><input id="campus" required></motionless><motionless class="form-group"><label>I am a</label><select id="role"><option value="student">Student Freelancer</option><option value="client">Client / Project Poster</option></select></motionless><motionless class="form-group"><label>Password</label><input type="password" id="password" required minlength="8"></motionless><button class="btn btn-primary" style="width:100%" type="submit">Create Account</button></form></motionless></section>
<script>
document.getElementById('reg-form').onsubmit = async (e) => {
  e.preventDefault();
  try {
    const data = await API.post('/auth/register', {
      full_name: document.getElementById('name').value,
      email: document.getElementById('email').value,
      campus: document.getElementById('campus').value,
      role: document.getElementById('role').value,
      password: document.getElementById('password').value
    });
    saveSession(data);
    showToast('Account created!', 'success');
    redirectByRole(data.user.role);
  } catch (err) { showToast(err.message, 'error'); }
};
</script>"""),
    "projects": ("Projects", "<section class='section container'><h1>Campus Projects</h1><motionless style='margin:1.5rem 0;display:flex;gap:1rem;flex-wrap:wrap'><input id='search' placeholder='Search projects...' style='flex:1;min-width:200px'><select id='status'><option value='open'>Open</option><option value='all'>All</option></select><button class='btn btn-primary' id='search-btn'>Search</button></motionless><motionless id='projects-list' class='grid grid-2'></motionless></section><script src='" + JS + "/public-projects.js'></script>"),
    "freelancers": ("Freelancers", "<section class='section container'><h1>Student Freelancers</h1><input id='q' placeholder='Search by skill or name' style='margin:1rem 0;width:100%;max-width:400px'><button class='btn btn-primary' id='search-btn'>Search</button><motionless id='list' class='grid grid-2' style='margin-top:2rem'></motionless></section><script>
async function load(){const q=document.getElementById('q').value;const data=await API.get('/users/freelancers?q='+encodeURIComponent(q));document.getElementById('list').innerHTML=data.map(f=>`<motionless class='glass card'><h3>${f.user?.full_name||'Student'}</h3><p>${f.headline||''}</p><p>⭐ ${f.rating_avg} · ${formatMoney(f.hourly_rate)}/hr</p><span class='badge'>${f.availability}</span></motionless>`).join('')||'<p>No freelancers found</p>';}
document.getElementById('search-btn').onclick=load;load();
</script>"),
}

for name, (title, body) in pages_public.items():
    public_page(name, title, body)

# Student dashboard pages
student_pages = {
    "dashboard.html": ("dashboard", "Dashboard", """
<div class="stats-grid" id="stats"></motionless>
<motionless class="glass card"><h2>AI Project Matches</h2><motionless id="matches" class="grid grid-2" style="margin-top:1rem"></motionless></motionless>
<script>
(async()=>{const u=getUser();document.getElementById('stats').innerHTML=`
<motionless class="glass stat-card"><motionless class="label">Role</motionless><motionless class="value">${u.role}</motionless></motionless>
<motionless class="glass stat-card"><motionless class="label">Campus</motionless><motionless class="value">${u.campus||'—'}</motionless></motionless>`;
try{const m=await API.get('/ai/project-matches');document.getElementById('matches').innerHTML=m.map(x=>`<motionless class="card glass"><h3>${x.project.title}</h3><p>Match: ${x.match_score}%</p><a href="projects.html">View</a></motionless>`).join('')||'<p>No matches yet</p>';}catch(e){}})();
</script>"""),
    "projects.html": ("projects", "Browse Projects", "<motionless id='list' class='grid grid-2'></motionless><script>API.get('/projects?status=open').then(d=>{document.getElementById('list').innerHTML=d.map(p=>`<motionless class='glass card'><h3>${p.title}</h3><p>${p.description.substring(0,120)}...</p><p><strong>${formatMoney(p.budget)}</strong></p><button class='btn btn-primary btn-sm' onclick='apply(${p.id})'>Apply</button> <button class='btn btn-ghost btn-sm' onclick='save(${p.id})'>Save</button></motionless>`).join('')});async function apply(id){const cover=prompt('Cover letter:');if(!cover)return;await API.post(`/projects/${id}/apply`,{cover_letter:cover});showToast('Applied!','success');}async function save(id){await API.post('/projects/saved',{project_id:id});showToast('Saved','success');}</script>"),
    "applications.html": ("applications", "My Applications", "<motionless id='list'></motionless><script>API.get('/projects/applications/my').then(d=>{document.getElementById('list').innerHTML='<motionless class=\"table-wrap glass\"><table><tr><th>Project</th><th>Status</th><th>Date</th></tr>'+d.map(a=>`<tr><td>${a.project_title}</td><td><span class='badge'>${a.status}</span></td><td>${formatDate(a.created_at)}</td></tr>`).join('')+'</table></motionless>';});</script>"),
    "messages.html": ("messages", "Messages", """<motionless class="chat-layout glass"><motionless class="chat-list" id="conv-list"></motionless><motionless class="chat-window glass"><motionless class="chat-messages" id="msgs"></motionless><motionless class="chat-input"><input id="msg-input" placeholder="Type a message..."><button class="btn btn-primary" id="send-btn">Send</button></motionless></motionless></motionless>
<script>
let currentConv=null;
async function loadConvs(){const c=await API.get('/chat/conversations');document.getElementById('conv-list').innerHTML=c.map(x=>`<motionless class="card" style="cursor:pointer;padding:0.75rem;margin-bottom:0.5rem" onclick="openConv(${x.id})"><strong>${x.other_user?.full_name||'User'}</strong><p style="font-size:0.85rem;color:var(--text-secondary)">${x.last_message?.content||''}</p></motionless>`).join('');}
async function openConv(id){currentConv=id;joinConversation(id);const msgs=await API.get(`/chat/conversations/${id}/messages`);const uid=getUser().id;document.getElementById('msgs').innerHTML=msgs.map(m=>`<motionless class="msg ${m.sender_id===uid?'sent':'received'}">${m.content}</motionless>`).join('');document.getElementById('msgs').scrollTop=9999;}
onNewMessage(m=>{if(m.conversation_id===currentConv) openConv(currentConv);});
document.getElementById('send-btn').onclick=()=>{const t=document.getElementById('msg-input').value;if(t&&currentConv){sendSocketMessage(currentConv,t);document.getElementById('msg-input').value='';}};
loadConvs();
</script>"""),
    "notifications.html": ("notifications", "Notifications", "<motionless id='list'></motionless><script>API.get('/notifications').then(n=>{document.getElementById('list').innerHTML=n.map(x=>`<motionless class='glass card' style='margin-bottom:0.5rem;opacity:${x.is_read?0.7:1}'><h3>${x.title}</h3><p>${x.message}</p></motionless>`).join('');API.put('/notifications/read-all',{});});</script>"),
    "earnings.html": ("earnings", "Earnings", "<motionless id='stats' class='stats-grid'></motionless><script>API.get('/auth/me').then(u=>{const p=u.profile||{};document.getElementById('stats').innerHTML=`<motionless class='glass stat-card'><motionless class='label'>Total Earnings</motionless><motionless class='value'>${formatMoney(p.total_earnings)}</motionless></motionless><motionless class='glass stat-card'><motionless class='label'>Rating</motionless><motionless class='value'>⭐ ${p.rating_avg||0}</motionless></motionless>`;});</script>"),
    "portfolio.html": ("portfolio", "Portfolio", """<form id='pf-form' class='glass card' style='padding:1.5rem;margin-bottom:1.5rem'><h3>Add Portfolio Item</h3><input name='title' placeholder='Title' required style='margin:0.5rem 0'><textarea name='description' placeholder='Description'></textarea><input type='file' name='file'><button class='btn btn-primary'>Add</button></form><motionless id='list' class='grid grid-2'></motionless>
<script>async function load(){const d=await API.get('/users/portfolio');document.getElementById('list').innerHTML=d.map(i=>`<motionless class='glass card'><h3>${i.title}</h3><p>${i.description||''}</p></motionless>`).join('');}
document.getElementById('pf-form').onsubmit=async e=>{e.preventDefault();const fd=new FormData(e.target);await API.upload('/users/portfolio',fd);showToast('Added','success');load();};
load();</script>"""),
    "reviews.html": ("reviews", "Reviews", "<motionless id='list'></motionless><script>API.get('/auth/me').then(u=>API.get('/projects/reviews/'+u.id)).then(d=>{document.getElementById('list').innerHTML=d.map(r=>`<motionless class='glass card'><p>⭐ ${r.rating} by ${r.reviewer_name}</p><p>${r.comment||''}</p></motionless>`).join('');});</script>"),
    "settings.html": ("settings", "Settings", """<motionless class='glass card' style='padding:2rem;max-width:500px'><h2>Profile Settings</h2><form id='set-form'><motionless class='form-group'><label>Bio</label><textarea id='bio'></textarea></motionless><motionless class='form-group'><label>Headline</label><input id='headline'></motionless><button class='btn btn-primary'>Save</button></form><button class='btn btn-outline' style='margin-top:1rem' id='ai-summary'>Generate AI Summary</button><p id='summary'></p></motionless>
<script>API.get('/users/profile').then(p=>{document.getElementById('bio').value=p.bio||'';document.getElementById('headline').value=p.headline||'';});
document.getElementById('set-form').onsubmit=async e=>{e.preventDefault();await API.put('/users/profile',{bio:document.getElementById('bio').value,headline:document.getElementById('headline').value});showToast('Saved','success');};
document.getElementById('ai-summary').onclick=async()=>{const r=await API.post('/ai/profile-summary',{});document.getElementById('summary').textContent=r.summary;};
</script>"""),
}

for fn, (active, title, body) in student_pages.items():
    dash_page("student", fn, title, active, body)

# Client pages
client_pages = {
    "dashboard.html": ("dashboard", "Client Dashboard", "<motionless class='stats-grid' id='stats'></motionless><motionless id='projects' class='grid grid-2'></motionless><script>API.get('/projects/my').then(p=>{document.getElementById('stats').innerHTML=`<motionless class='glass stat-card'><motionless class='label'>Projects</motionless><motionless class='value'>${p.length}</motionless></motionless>`;document.getElementById('projects').innerHTML=p.slice(0,4).map(x=>`<motionless class='glass card'><h3>${x.title}</h3><span class='badge'>${x.status}</span></motionless>`).join('');});</script>"),
    "post-project.html": ("post-project", "Post Project", """<form id='form' class='glass card' style='padding:2rem;max-width:600px'><motionless class='form-group'><label>Title</label><input id='title' required></motionless><motionless class='form-group'><label>Description</label><textarea id='desc' rows='5' required></motionless><motionless class='form-group'><label>Budget ($)</label><input type='number' id='budget' required></motionless><motionless class='form-group'><label>Deadline</label><input type='date' id='deadline'></motionless><button class='btn btn-primary'>Post Project</button></form>
<script>document.getElementById('form').onsubmit=async e=>{e.preventDefault();await API.post('/projects',{title:document.getElementById('title').value,description:document.getElementById('desc').value,budget:document.getElementById('budget').value,deadline:document.getElementById('deadline').value});showToast('Posted!','success');location.href='manage-projects.html';};</script>"""),
    "manage-projects.html": ("manage-projects", "Manage Projects", "<motionless id='list' class='grid grid-2'></motionless><script>API.get('/projects/my').then(d=>{document.getElementById('list').innerHTML=d.map(p=>`<motionless class='glass card'><h3>${p.title}</h3><p>${formatMoney(p.budget)} · ${p.status}</p><input type='range' min='0' max='100' value='${p.progress}' onchange='updateProgress(${p.id},this.value)'><a href='applicants.html?project=${p.id}'>Applicants (${p.application_count})</a></motionless>`).join('');});async function updateProgress(id,v){await API.put(`/projects/${id}`,{progress:v});}</script>"),
    "applicants.html": ("applicants", "Applicants", "<motionless id='list'></motionless><script>const pid=new URLSearchParams(location.search).get('project');API.get(`/projects/${pid}/applications`).then(apps=>{document.getElementById('list').innerHTML=apps.map(a=>`<motionless class='glass card'><h3>${a.applicant_name}</h3><p>${a.cover_letter}</p><button class='btn btn-primary btn-sm' onclick='decide(${a.id},\"accepted\")'>Accept</button> <button class='btn btn-ghost btn-sm' onclick='decide(${a.id},\"rejected\")'>Reject</button></motionless>`).join('');});async function decide(id,s){await API.put(`/projects/applications/${id}`,{status:s});showToast('Updated','success');location.reload();}</script>"),
    "messages.html": ("messages", "Messages", "<p>Same as student messages — open a conversation from applicants.</p><script>location.href='/frontend/pages/student/messages.html';</script>"),
    "payments.html": ("payments", "Payments", "<motionless id='list'></motionless><script>API.get('/projects/my').then(async ps=>{let html='';for(const p of ps){if(p.status==='in_progress')html+=`<motionless class='glass card'><h3>${p.title}</h3><button class='btn btn-primary' onclick='pay(${p.id},${p.hired_freelancer_id||0})'>Record Payment</button></motionless>`;}document.getElementById('list').innerHTML=html||'<p>No active projects</p>';});async function pay(pid,payee){const amt=prompt('Amount:');if(amt)await API.post(`/projects/${pid}/payments`,{amount:amt,payee_id:payee});showToast('Recorded','success');}</script>"),
    "analytics.html": ("analytics", "Analytics", "<motionless class='stats-grid'><motionless class='glass stat-card'><motionless class='label'>Projects Posted</motionless><motionless class='value' id='c'>—</motionless></motionless></motionless><script>API.get('/projects/my').then(p=>document.getElementById('c').textContent=p.length);</script>"),
    "saved.html": ("saved", "Saved Freelancers", "<motionless id='list' class='grid grid-2'></motionless><script>API.get('/users/saved-freelancers').then(d=>{document.getElementById('list').innerHTML=d.map(f=>`<motionless class='glass card'><h3>${f.user?.full_name}</h3><p>${f.headline}</p></motionless>`).join('');});</script>"),
    "settings.html": ("settings", "Settings", "<motionless class='glass card' style='padding:2rem'><form id='f'><input id='name'><button class='btn btn-primary'>Save</button></form></motionless><script>const u=getUser();document.getElementById('name').value=u.full_name;document.getElementById('f').onsubmit=async e=>{e.preventDefault();await API.put('/users/settings',{full_name:document.getElementById('name').value});showToast('Saved','success');};</script>"),
}

for fn, (active, title, body) in client_pages.items():
    dash_page("client", fn, title, active, body)

# Admin pages
admin_pages = {
    "dashboard.html": ("dashboard", "Admin Dashboard", "<motionless class='stats-grid' id='stats'></motionless><script>API.get('/admin/dashboard').then(s=>{document.getElementById('stats').innerHTML=Object.entries(s).map(([k,v])=>`<motionless class='glass stat-card'><motionless class='label'>${k}</motionless><motionless class='value'>${v}</motionless></motionless>`).join('');});</script>"),
    "users.html": ("users", "Users", "<motionless class='table-wrap glass'><table id='t'><tr><th>Name</th><th>Email</th><th>Role</th><th>Actions</th></tr></table></motionless><script>API.get('/admin/users').then(u=>{document.getElementById('t').innerHTML+='<tr>'+u.map(x=>`<tr><td>${x.full_name}</td><td>${x.email}</td><td>${x.role}</td><td><button onclick='ban(${x.id})'>Ban</button></td></tr>`).join('')});async function ban(id){await API.put(`/admin/users/${id}`,{is_banned:true});showToast('Banned','success');}</script>"),
    "reports.html": ("reports", "Reports", "<motionless id='list'></motionless><script>API.get('/admin/reports').then(r=>{document.getElementById('list').innerHTML=r.map(x=>`<motionless class='glass card'><p>${x.reason}</p><button onclick='resolve(${x.id})'>Resolve</button></motionless>`).join('');});async function resolve(id){await API.put('/admin/reports',{report_id:id,status:'resolved'});}</script>"),
    "analytics.html": ("analytics", "Analytics", "<motionless id='stats' class='stats-grid'></motionless><script>API.get('/admin/dashboard').then(s=>{document.getElementById('stats').innerHTML=Object.entries(s).map(([k,v])=>`<motionless class='glass stat-card'><motionless class='label'>${k}</motionless><motionless class='value'>${v}</motionless></motionless>`).join('');});</script>"),
    "categories.html": ("categories", "Categories", "<form id='cf' class='glass card' style='padding:1rem;margin-bottom:1rem'><input id='cname' placeholder='Category name'><button class='btn btn-primary'>Add</button></form><motionless id='list'></motionless><script>async function load(){const c=await API.get('/admin/categories');document.getElementById('list').innerHTML=c.map(x=>`<motionless class='badge'>${x.name}</motionless> `).join('');}document.getElementById('cf').onsubmit=async e=>{e.preventDefault();await API.post('/admin/categories',{name:document.getElementById('cname').value});load();};load();</script>"),
    "revenue.html": ("revenue", "Revenue", "<motionless class='glass stat-card'><motionless class='label'>Total Revenue</motionless><motionless class='value' id='rev'>—</motionless></motionless><script>API.get('/admin/dashboard').then(s=>document.getElementById('rev').textContent=formatMoney(s.revenue));</script>"),
    "verification.html": ("verification", "Verification", "<motionless id='list'></motionless><script>API.get('/admin/verifications').then(v=>{document.getElementById('list').innerHTML=v.map(x=>`<motionless class='glass card'>User #${x.user_id} <button onclick='approve(${x.id})'>Approve</button></motionless>`).join('')||'<p>None pending</p>';});async function approve(id){await API.put('/admin/verifications',{id,status:'approved'});location.reload();}</script>"),
}

for fn, (active, title, body) in admin_pages.items():
    dash_page("admin", fn, title, active, body)

print("Done generating pages")
