import telnetlib
import click
import json

# TODO: support for multiple files

@click.command()
@click.option('--host', default="localhost", prompt="Host")
@click.option('--file', type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True, resolve_path=True))
def inject(host, file):
	path = file
	with open(path, "r") as f:
		file = f.read()
	filename = path.split("/")[-1]
	tn = telnetlib.Telnet(host, 43250)
	tn.read_until(b"bombsquad>")
	print("host available")
	while 1:
		try:
			tn.write(b"42\n")
			d = tn.read_until(b"42", timeout=5).decode("utf-8")
			print(d)
			if "42" in d:
				break
		except EOFError:
			print("telnet not allowed")
	print("telnet allowed")

	def send_line(line):
		print(line)
		tn.write(bytes(line, encoding="ascii"))
		d = tn.read_until(b"bombsquad>", timeout=1).decode("utf-8")
		if len(d.replace("bombsquad>", "")) > 1:
			print(">", d)

	setup = """
import bs, json, os
from md5 import md5
mods_folder = bs.getEnvironment()['userScriptsDirectory'] + "/"
bs.playSound(bs.getSound("gunCocking"))
bs.screenMessage("sending data")
d = ""
"""[1:]
	for line in setup.split("\n"):
		send_line(line)
	data = json.dumps(file)[1:-1]
	chunksize = 250
	pos = 0
	buf = ""
	while pos < len(data):
		buf += data[pos]
		pos += 1
		if len(buf) > chunksize and not buf[-1] == "\\" or pos >= len(data):
			send_line('d += """{}"""'.format(buf.replace('"""', '\"\"\"')))
			buf = ""

	send_line("bs.screenMessage('data sent')")
	send_line("md5(d).hexdigest()") # FIXME: actually check md5

	if click.confirm('Save to mods folder?', default=True):
		send_line("path = mods_folder + '{}'".format(filename))
		#send_line("os.rename(path, path + '.bak')")
		send_line("f = open(path, 'w')")
		send_line("f.write(d)")
		send_line("f.close()")
	if click.confirm('Exec?'):
		send_line("exec(d)")
	if click.confirm("Quit?", default=True):
		send_line("bs.quit()")

	#tn.interact()

	tn.close()

if __name__ == '__main__':
	inject()
