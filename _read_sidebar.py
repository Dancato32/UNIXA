with open('community/templates/community/nexa_home.html','rb') as f:
    raw = f.read()
c = raw.decode('utf-8','replace')

# Find the main nx-sidebar HTML
idx = c.find('id="nx-sidebar"')
print(c[idx:idx+4000])
