######
# Developed by:	David Astvatsatryan
# Date:		June 2020
# Version:	2.0
# Memory Compiler Engineering Team
# Usage:	python template_update.py absolute_path_of_complib
######

import logging, sys, os, stat, re
from subprocess import Popen, PIPE, STDOUT

abort = "\nINFO:\tAborting due to above error"

class Tmpupdate:
#	sys.tracebacklimit = 0
	
	
	def __init__(self, path):
	
		self.path = path.rstrip("/")
		

#Code logger
	def logfile(self):

		self.partname = self.path.split("/")
		self.root = "/".join(self.partname[:-3])
		(output_mkdir, error_mkdir) = Popen(["mkdir", self.root + "/template_update"], stdout=PIPE, stderr=PIPE).communicate()
		log_file = self.root + "/template_update/template_update.log"
		(output_log, error_log) = Popen(["touch", log_file], stdout=PIPE, stderr=PIPE).communicate()
		logger = logging.basicConfig(filename=log_file, filemode='w', level=logging.DEBUG, format='%(levelname)s:\t%(message)s')
		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)
		formatter = logging.Formatter('%(levelname)s:\t%(message)s')
		ch.setFormatter(formatter)
		logging.getLogger('').addHandler(ch)
		logger = logging.getLogger(__name__)
		
		logging.info('Starting template update code')


#check if there is header.tpl, glb and prm in your path
#if no raise exception
	def exist_check(self):
		self.file_lst = ["header.tpl", self.partname[-1] + ".glb", self.partname[-1] + "_custom.glb", self.partname[-1] + ".prm", "check.rtb"]
		for i in self.file_lst:
			header = os.path.isfile(self.path + "/" + i)

			if header:
				logging.info('File exists in {}'.format(self.path + "/" + i))
			else:
				logging.error(i + " do not exist in " + self.path + abort)
				raise Exception( i + " do not exist in " + self.path + abort)
				
		logging.info('All necessary input files are found for template update')

#checks if depot is set from terminal
#if no raise exception
	def depot_check(self):
		stream_depo = os.popen('echo $PIPE_P4_DEPOT')
		out_depo = stream_depo.read()

		if out_depo == "\n":
			logging.error('PIPE_P4_DEPOT is undefined, please define it and rerun' + abort)
			raise NameError ('PIPE_P4_DEPOT is undefined, please define it and rerun' + abort)
			
		logging.info('Depot seted to ' + str(out_depo).strip())


#searches setting.tcl by useing deslib name in argument
#if didnt find raise exception 
	def searcher(self):
		data_path = ""
		modules = self.root + "/modules"
		for mpath, dirs, files in os.walk(modules):
			if self.partname[-2] in dirs:
				data_path = os.path.join(mpath, self.partname[-2])

		if os.path.isdir(data_path):
			None		
		else:
			logging.error('your deslib ' +  self.partname[-2] + ' do not exist in modules directory' + abort)
			raise NameError ( "your deslib " +  self.partname[-2] + " do not exist in modules directory" + abort)

		self.setting = data_path + "/data/setting.tcl"

		self.deslib = self.setting.split("/")[-3]
		self.module = self.setting.split("/")[-4]
		
		if os.path.exists(self.setting):
			logging.info('File exists in {}'.format(self.setting))
		else:
			logging.error('setting.tcl not found inside data directory' + abort)
			raise NameError ( "setting.tcl not found inside data directory" + abort)
			sys.exit(1)

		logging.info('Module and setting.tcl are present in sendbox')

#Checking permission of flies
	def permission(self):
		self.true_answers = ["yes", "y"]
		self.false_answers = ["no", "n"]
		
		glb = self.path + "/" + self.partname[-1] + ".glb"
		prm = self.path + "/" + self.partname[-1] + ".prm"
		custom_glb = self.path + "/" + self.partname[-1] + "_custom.glb"

		non_writabel = []
		for i in [glb, custom_glb, prm, self.setting]:
			if os.access(i, os.W_OK):
				None
			else:
				non_writabel.append(i)
				
		if len(non_writabel) != 0:
			answer = None	
			while answer not in ["yes", "y", "no", "n"]:
				answer = raw_input("you are not permitted to change below files.\n {} \nDo you want to change permission of this files? :  ".format(", ".join([i for i in non_writabel])))
				if answer in self.true_answers:
					for i in non_writabel:
						logging.info('Opening permission for {}'.format(i))
						try:
							os.chmod(i, 0o777)
						except IOError:
							logging.error('You are not eligible to change permission of this file {}'.format(i) + abort)
							sys.exit(1)
				
				elif answer in self.false_answers:
					logging.error('No permission to change below files' + abort)
					logging.info('{}'.format(", ".join([i for i in non_writabel])))
					raise Exception( "No permission to change below files" + abort)

				else:
					print("Please enter yes/no or y/n")

		logging.info('There is no permission issue to write files')

#parse setting.tcl to find rel_number, module, deslib
#raise exception if setting.tcl is currupted
#setting piperoot, loging in, checking edoc information ()
	def settingtcl_parse(self):
		logging.info('Setting up correct PIPEROOT evniroment from terminal, PIPEROOT is set to')
		logging.info(self.root)
		
		os.environ["PIPEROOT"] = self.root
		os.environ["QUERYCCS_ENABLE"] = "1"
		stream_root_login = Popen(["pipe", "-login"], stdout=PIPE, stderr=PIPE)
		out_root_login, err_root_login = stream_root_login.communicate()

		logging.info('Loading emll_cadutilities_queryccs')
		(output, error) = Popen(['/usr/bin/modulecmd', 'python'] +  ['unload'] + ['emll_cadutilities_queryccs'], stdout=PIPE).communicate()
		(output, error) = Popen(['/usr/bin/modulecmd', 'python'] +  ['load'] + ['emll_cadutilities_queryccs'], stdout=PIPE).communicate()
		
		logging.info('Unloading and loading embedit')		
		(output, error) = Popen(['/usr/bin/modulecmd', 'python'] +  ['unload'] + ['embedit'], stdout=PIPE).communicate()
		(output, error) = Popen(['/usr/bin/modulecmd', 'python'] +  ['load'] + ['embedit'], stdout=PIPE).communicate()
		
		with open (self.setting, "r") as f:
			f = f.readlines()
		
		for line in f:
			if re.match("(.*)queryccs_rel(.*)", line):
				rel_line = line
			elif re.match("(.*)set edoclib (.*)", line):
				edoc_line = line.split()[-1]
			elif re.match("(.*)set tpllib (.*)", line):
				self.template_line = line.split()[-1].split("/")[-1]
			elif re.match("(.*)set tpllibtag (.*)", line):
				self.old_tpllib = line.split()[-1]
				
		#checking rel number existance in setting.tcl
		if len(rel_line.split()) != 3:
			logging.error('Setting.tcl is corrupted or there is no rel number ')
			logging.info(rel_line + abort)
			raise NameError ( "Setting.tcl is corrupted or there is no rel number " + "\n\n"  + rel_line + abort)
		
		else:
			self.rel = rel_line.split()[-1]

		#checking edoclib existance in setting.tcl. checking if edoclib exists in piperoot if not getting it. 
		#if in P4 this edoclib not exist aborting run to set correct depot or check edoclib path in setting.tcl		
		if len(rel_line.split()) != 3:
			logging.error('Setting.tcl is corupted or there is no edoclib information ')
			logging.info(edoc_line + abort)
			
			raise NameError ( "Setting.tcl is corupted or there is no edoclib information " + "\n\n"  + edoc_line + abort)
		elif os.path.exists(self.root+"/"+edoc_line):
			logging.info('Edoclib present in piperoot')

		#in this portion I am checking if depot is correct
		stream_edoclib = Popen(['pipe', '-get', self.root + "/"+ edoc_line], stdout=PIPE, stderr=PIPE)
		stdout, stderr = stream_edoclib.communicate()
		if "No such file or directory" in stderr:
			logging.error('Most probably depot is incorrect or edoclib path in setting.tcl is incorrect '+ abort)
			raise NameError ( "Most probably depot is incorrect or edoclib path in setting.tcl is incorrect " + abort)

		elif "Please run pipe -login at first" in stderr:
			logging.info('Running pipe login to proceed')
			stream_login = Popen(["pipe", "-login"], stdout=PIPE, stderr=PIPE)
			stdout_login, stderr_login = stream_login.communicate()
		else:
			logging.info('Depot and setting.tcl inormation for edoc lib is correct')
			
		logging.info('Setting.tcl information needed for template update is correct')

#run taginfo and check current and latest rel versions		
	def taginfo(self):
		logging.info('Running taginfo')

		stream_tag = Popen(["pipe", "-taginfo", self.module, self.deslib], stdout=PIPE, stderr=PIPE)
		out_taginfo, err_taginfo = stream_tag.communicate()
		matches_info = re.compile('(?ms)(^\-.*?)(?=^\-)')
		info_parse = "".join([elem for elem in matches_info.findall(out_taginfo)])
		self.latest_tags = {}
		self.lib_names = []
		for i,line in enumerate(info_parse.split("\n")[3:-1]):
			splited = line.split()
			if splited[1] != splited[3]:
				self.lib_names.append(splited[0])
				self.latest_tags[splited[1]] = splited[3]
			
			if splited[0] == "tpllibtag":
				self.new_tpllib = splited[3]
				
		if bool(self.latest_tags):
			(output_rm_tcl, error_rm_tcl)  = Popen(["rm", "-rf", self.root + "/template_update/" + "setting.tcl"], stdout=PIPE, stderr=PIPE).communicate()
			(output_cp_tcl, error_cp_tcl)  = Popen(["cp", self.setting, self.root + "/template_update"], stdout=PIPE, stderr=PIPE).communicate()
			logging.info('Below libs need update in setting.tcl')
			for item in self.lib_names:
				logging.info(item)
			logging.info('Starting to update lib versions to latest tags')
		else:
			stream_rm_dir = Popen(["rm", "-rf", self.root + "/template_update"], stdout=PIPE, stderr=PIPE)
			logging.info('All lib versions are latest in setting.tcl, nothing to update')
			raise Exception( "Exiting code")



#setting.tcl update for all lib rel versions to latest
	def setting_update(self):
		lines = []
		with open(self.setting, "r") as set_tcl:
			for line in set_tcl:
				for src, target in self.latest_tags.iteritems():
					line = line.replace(src, target)
				lines.append(line)
		with open(self.setting, "w") as out:
			for line in lines:
				out.write(line)
				
		
		logging.info('setting.tcl is updated')		

	def tpllib_update_check(self):
		if "tpllibtag" in self.lib_names:
			tpllib_versions_func = self.tpllib_versions()
			update_files_func = self.update_files()
			add_remove_change_glb_func = self.add_remove_change_glb()
			add_remove_change_prm_func = self.add_remove_change_prm()
			shady_flags_func = self.shady_flags()
			backup_func = self.backup()
			add_remove_flag_prm_func = self.add_remove_flag_prm()
			add_remove_flag_glb_func = self.add_remove_flag_glb()
			add_remove_flag_custom_func = self.add_remove_flag_custom()
		else:
			logging.info('Template update is not required')

#get latest and current versions of tpllib and check the differences
	def tpllib_versions(self):

		self.old_template_path = self.root+"/tpllib/"+self.template_line+"_"+self.old_tpllib
		self.new_template_path = self.root+"/tpllib/"+self.template_line

		stream_rmtpllib = Popen(["rm", "-rf", self.new_template_path], stdout=PIPE, stderr=PIPE)
		stream_oldtpllib = Popen(["pipe", "-get", "-label", self.old_tpllib, self.new_template_path], stdout=PIPE, stderr=PIPE)
		out_get_old, err_get_old = stream_oldtpllib.communicate()
		stream_oldtpllib_mv = Popen(["mv", self.new_template_path, self.old_template_path], stdout=PIPE, stderr=PIPE)
		stream_newtpllib = Popen(["pipe", "-get", "-label", self.new_tpllib, self.new_template_path], stdout=PIPE, stderr=PIPE)
		out_get_new, err_get_new = stream_newtpllib.communicate()
		stream_diffing = Popen(["diff", "-qr", self.new_template_path, self.old_template_path], stdout=PIPE, stderr=PIPE)
		out_diff, err_diff = stream_diffing.communicate()
		files_update_bk = []
		files_missing = []
		self.removed_tpl = []
		self.added_tpl = []
		for line in out_diff.split("\n")[:-1]:
			if "Files" in line:
				tmp_name = line.split()
				tmp_name = tmp_name[-2].split("/")
				files_update_bk.append(tmp_name[-1])
			else:
				files_missing.append(line)
				
		for files in files_missing:
			if self.old_tpllib in files:
				old_tmp_name = files.split()
				self.removed_tpl.append(old_tmp_name[-1])
			else:
				new_tmp_name = files.split()
				self.added_tpl.append(new_tmp_name[-1])
		
		self.files_update = []				
		for tpl in files_update_bk:
			if "tpl" in tpl:
				self.files_update.append(tpl)
			elif "std_" in tpl:
				self.files_update.append(tpl)

		if len(self.files_update) != 0:
			logging.info('Below templates need update in complib')
			for i in self.files_update:
				logging.info('{}'.format(i))
		if len(self.removed_tpl)  != 0:
			logging.info('Below templates are removed from old version' + self.old_tpllib)
			for i in self.removed_tpl:
				logging.info(i)
		if len(self.added_tpl)  != 0:
			logging.info('Below templates are added in new version' + self.new_tpllib)
			for i in self.added_tpl:
				logging.info(i)
		
		logging.info('Template files are detected for update')


# In this part code will update template files in complib
	def update_files(self):
		if len(self.files_update) != 0:
			for tpl in self.files_update:
				stream_rmtpl = Popen(["rm", "-rf", self.path + "/" + tpl], stdout=PIPE, stderr=PIPE)
				stream_cptpl = Popen(["cp", self.new_template_path + "/" + tpl, self.path + "/" ], stdout=PIPE, stderr=PIPE)
				

		if len(self.removed_tpl)  != 0:
			for tpl in self.removed_tpl:
				stream_rmtpl = Popen(["rm", "-rf", self.path + "/" + tpl], stdout=PIPE, stderr=PIPE)

		if len(self.added_tpl)  != 0:
			for tpl in self.added_tpl:
				stream_cptpl = Popen(["cp", self.new_template_path + "/" + tpl, self.path + "/" ], stdout=PIPE, stderr=PIPE)
		
		logging.info('Complib is updated with new template files')	

# In this part code is chacking what is added, removed or changed in glb 
	def add_remove_change_glb(self):

		with open(self.old_template_path + "/template.glb", "r") as f:
			old_glb = f.read()

		with open(self.new_template_path + "/template.glb", "r") as f:
			new_glb = f.read()

		old_name_pattern_glb = re.compile('(?m)(.*\=)')
		old_name_find_glb = re.findall(pattern=old_name_pattern_glb, string=old_glb)

		new_name_pattern_glb = re.compile('(?m)(.*\=)')
		new_name_find_glb = re.findall(pattern=new_name_pattern_glb, string=new_glb)

		added_names_glb = []
		removed_names_glb = []
		self.added_flags_glb = []
		self.removed_flags_glb = []
		for i, flag in enumerate(old_name_find_glb):
			if flag not in new_name_find_glb:
				removed_names_glb.append(flag)
		
		for i, flag in enumerate(new_name_find_glb):
			if flag not in old_name_find_glb:
				added_names_glb.append(flag)
		
		old_flags_glb = []
		new_flags_glb = []
		for flag in old_name_find_glb:
			old_flag_pattern_glb = re.compile('(?ms)(' + re.escape(flag) + '.*?)(?=^\S)')
			old_flag_find_glb = re.findall(pattern=old_flag_pattern_glb, string=old_glb)
			old_flags_glb.append(old_flag_find_glb)

		for flag in new_name_find_glb:
			new_flag_pattern_glb = re.compile('(?ms)(' + re.escape(flag) + '.*?)(?=^\S)')
			new_flag_find_glb = re.findall(pattern=new_flag_pattern_glb, string=new_glb)
			new_flags_glb.append(new_flag_find_glb)

		
		#Flattering *flags_glb for diffing 
		flatten_old_glb = [item for sublist in old_flags_glb for item in sublist]
		flatten_new_glb = [item for sublist in new_flags_glb for item in sublist]

		for name in set(removed_names_glb):
			for flag in flatten_old_glb:
				if name in flag:
					self.removed_flags_glb.append(flag)
					
		for name in set(added_names_glb):
			for flag in flatten_new_glb:
				if name in flag:
					self.added_flags_glb.append(flag)
		
		self.removed_flags_glb = list(set(self.removed_flags_glb))
		self.added_flags_glb = 	list(set(self.added_flags_glb))		
		self.changed_flags_glb = []
		changed_flags_glb_a = list(set(flatten_old_glb) - set(flatten_new_glb))
		changed_flags_glb_b = list(set(flatten_new_glb) - set(flatten_old_glb))
		changed_flags_glb_c = list(set(changed_flags_glb_a + changed_flags_glb_b))
		
		
		for item in changed_flags_glb_c:
			if item not in self.added_flags_glb + self.removed_flags_glb:
				self.changed_flags_glb.append(item)
				
		self.changed_flags_glb_new = self.changed_flags_glb[0::2]
			
# In this part, code is chacking what is added, removed or changed in prm 

	def add_remove_change_prm(self):
		with open(self.old_template_path + "/template.prm", "r") as f:
			old_prm = f.read()

		with open(self.new_template_path + "/template.prm", "r") as f:
			new_prm = f.read()

		old_pattern_prm = re.compile('(?ms)(name.*?)(?=\/)')
		old_find_prm = re.findall(pattern=old_pattern_prm, string=old_prm)
		old_name_pattern_prm = re.compile('(?m)(name\=.*)')
		old_name_find_prm = re.findall(pattern=old_name_pattern_prm, string=old_prm)
		
		new_pattern_prm = re.compile('(?ms)(name.*?)(?=\/)')
		new_find_prm = re.findall(pattern=new_pattern_prm, string=new_prm)
		new_name_pattern_prm = re.compile('(?m)(name\=.*)')
		new_name_find_prm = re.findall(pattern=new_name_pattern_prm, string=new_prm)
		
		self.added_names_prm = []
		self.removed_names_prm = []
		self.added_flags_prm = []
		self.removed_flags_prm = []
		for i, flag in enumerate(old_name_find_prm):
			if flag not in new_name_find_prm:
				self.removed_names_prm.append(flag)
				self.removed_flags_prm.append(old_find_prm[i])
		
		for i, flag in enumerate(new_name_find_prm):
			if flag not in old_name_find_prm:
				self.added_names_prm.append(flag)
				self.added_flags_prm.append(new_find_prm[i])
		
		self.changed_flags_prm = []
		changed_flags_prm_a = list(set(old_find_prm) - set(new_find_prm))
		changed_flags_prm_b = list(set(new_find_prm) - set(old_find_prm))
		changed_flags_prm_c = list(set(changed_flags_prm_a + changed_flags_prm_b))
		
		for item in changed_flags_prm_c:
			if item not in self.added_flags_prm + self.removed_flags_prm:
				self.changed_flags_prm.append(item)
		
		self.changed_flags_prm_new = self.changed_flags_prm[0::2]
		self.changed_flags_prm_old = self.changed_flags_prm[1::2]

		self.added_user_falgs = []
		self.removed_user_falgs = []
		
		for flag in self.added_flags_prm + self.changed_flags_prm_new:
			if "level_edit=\"USER\"" in flag:
				self.added_user_falgs.append(flag.split()[0].split("=")[-1].strip("\""))

		for flag in self.removed_flags_prm + self.changed_flags_prm_old:
			if "level_edit=\"USER\"" in flag:
				self.removed_user_falgs.append(flag.split()[0].split("=")[-1].strip("\""))
			

		

# In this part code will detect shady flags which can be for different node and ask user for clarification
	def shady_flags(self):
		squishy_remove = []
		squishy_add = []
		for line in self.removed_flags_glb:
			if "only" in line:
				squishy_remove.append(line)
				
		for line in self.added_flags_glb:
			if "only" in line:
				squishy_add.append(line)
		
		if len(squishy_remove) != 0:
			print("\n" + "Please review below flag with description and answer if you want this flag to be removed from glb/prm and/or custom.glb" + "\n" /
					+ "It can be removed for different node" + "\n")
			for flag in squishy_remove:
				print("\n".join([i for i in flag.split("\n")]))
				answer = None
				while answer not in ["yes", "y", "no", "n"]:
					answer = raw_input("Do you want to remove this flag from glb (yes/no)/(y/n): ").strip()
					if answer in self.true_answers:
						self.removed_flags_glb.remove(flag)
						
						flag_name = flag.split("=")[0].strip()
						self.removed_flags_glb.remove(flag)

						if flag_name in self.added_user_falgs:
							self.removed_user_falgs.remove(flag_name)

						for block in self.removed_flags_prm:
							if flag_name in block:
								self.added_flags_prm.remove(block)
					elif answer in self.false_answers:
						None
					else:
						print("Please enter yes/no or y/n")

		if len(squishy_add) != 0:
			print("\n" + "Please review below flag with description and answer if you want this flag to be added in glb/prm and/or custom.glb" + "\n" + "It can be required for different node" + "\n")
			for flag in squishy_add:
				print("\n".join([i for i in flag.split("\n")]))
				answer = None
				while answer not in ["yes", "y", "no", "n"]:
					answer = raw_input("Do you want to add this flag to glb (yes/no)/(y/n): ").strip()
					if answer in self.true_answers:
						None
					elif answer in self.false_answers:
						flag_name = flag.split("=")[0].strip()
						self.added_flags_glb.remove(flag)

						if flag_name in self.added_user_falgs:
							self.added_user_falgs.remove(flag_name)

						for block in self.added_flags_prm:
							if flag_name in block:
								self.added_flags_prm.remove(block)
					else:
						print("Please enter yes/no or y/n")

				
# Function to backup files
	def backup(self):
		if len(self.removed_flags_prm) + len(self.added_flags_prm) + \
			len(self.removed_flags_glb) + len(self.added_flags_glb) != 0:
			
			logging.info('Creating backup of changed files for your referance in below directory')
			logging.info(self.root + '/template_update')

#add/removing flags from prm
	def add_remove_flag_prm(self):
		if len(self.removed_flags_prm) + len(self.added_flags_prm) != 0:
			(output_rm_prm, error_rm_prm)  = Popen(["rm", "-rf", self.root + "/template_update/" + self.partname[-1] + ".prm"], stdout=PIPE, stderr=PIPE).communicate()
			(output_cp_prm, error_cp_prm)  = Popen(["cp", self.path + "/" + self.partname[-1] + ".prm", self.root + "/template_update"], stdout=PIPE, stderr=PIPE).communicate()
			
		with open(self.path + "/" + self.partname[-1] + ".prm", "r") as prm_in:
			block_prm = prm_in.read()
			if len(self.removed_names_prm) != 0:
				for flag in self.removed_names_prm + self.added_names_prm:
					rm_pattern = re.compile('(?s)(\<parameter\s+' + re.escape(flag) + '.*?)(?:\/\>){1}')
					rm_flag = re.findall(pattern=rm_pattern, string=block_prm)
					block_prm = re.sub(pattern=rm_pattern, string=block_prm, repl="")

			if len(self.changed_flags_prm) != 0:
				for i, flag in enumerate(self.changed_flags_prm_old):
					name = flag.split()[0]
					change_pattern = re.compile('(?s)(\<parameter\s+' + re.escape(name) + '.*?)(?:\/\>){1}')
					change_flag = re.findall(pattern=change_pattern, string=block_prm)
					block_prm = re.sub(pattern=change_pattern, string=block_prm, repl="<parameter\n  " + self.changed_flags_prm_old[i] + "\n/>\n")
					
			block_prm = re.sub(pattern='\<\/parameter_list\>', string=block_prm, repl="")		
				
				
		with open(self.path + "/" + self.partname[-1] + ".prm", "w") as prm_out:
			prm_out.write(block_prm)
			if len(self.added_flags_prm) != 0:
				for flag in self.added_flags_prm:
					prm_out.write("<parameter\n  " + flag + "\n/>\n")
			
			prm_out.write("\n"+"</parameter_list>")

		logging.info('Compiler.prm is updated')


#add/removing flags from glb
	def add_remove_flag_glb(self):

		if len(self.removed_flags_glb) + len(self.added_flags_glb) != 0:
			(output_rm_glb, error_rm_glb)  = Popen(["rm", "-rf", self.root + "/template_update/" + self.partname[-1] + ".glb"], stdout=PIPE, stderr=PIPE).communicate()
			(output_cp_glb, error_cp_glb)  = Popen(["cp", self.path + "/" + self.partname[-1] + ".glb", self.root + "/template_update"], stdout=PIPE, stderr=PIPE).communicate()
	
		with open(self.path + "/" + self.partname[-1] + ".glb", "r") as glb_in:
			block_glb = glb_in.read()
			if len(self.removed_flags_glb) != 0:
				for line in self.removed_flags_glb:
					rm_pattern_glb = re.compile('(?ms)((%s).*?)(?=^\S)'%line.split("=")[0])
					rm_line = re.findall(pattern=rm_pattern_glb, string=block_glb)
					block_glb = re.sub(pattern=rm_pattern_glb, string=block_glb, repl="")
			
			if len(self.added_flags_glb) != 0:
				for line in self.added_flags_glb:
					rm_pattern_glb = re.compile('(?ms)((%s).*?)(?=^\S)'%line.split("=")[0])
					rm_line = re.findall(pattern=rm_pattern_glb, string=block_glb)
					block_glb = re.sub(pattern=rm_pattern_glb, string=block_glb, repl="")

				pattern_tpl = re.compile('(?ms)(template[0-9] .*:?)(template.*\/\" \})')
				tpl_line = re.findall(pattern=pattern_tpl, string=block_glb)
				tpl_block = ",".join(["".join(tup) for tup in tpl_line])
				tpl_block_spl = tpl_block.split("\n")
				tpl_nums = []
				added_tpl_num = []
				added_tpl = []
				added_flags = []
				for line in tpl_block_spl:
					tpl_nums.append(line.split("=")[0].split("template")[1])

				for item in set(self.added_flags_glb):
					added_flags.append(item)
#					if "template" in item:
#						print("this is item ------------------------", item)
#						added_tpl_num.append(item.split("=")[0].split("template")[1])
#						added_tpl.append(item)
#					else:
#						added_flags.append(item)
					
				for i, num in enumerate(added_tpl_num):
					position = 1
					for pos in tpl_nums:
						if num > pos:
							position += 1
							
					tpl_block_spl = tpl_block_spl[:position] + [added_tpl[i].rstrip()] + tpl_block_spl[position:]

				block_glb = re.sub(pattern=pattern_tpl, string=block_glb, repl="\n".join(tpl_block_spl))
				
				pattern_flags = re.compile('(?m)(pf_leafcell_prefix .*:?)')
				flags_line = re.findall(pattern=pattern_flags, string=block_glb)
				flags_block = ",".join(["".join(tup) for tup in flags_line])
				combined_flags = "\n".join(added_flags + [flags_block])
				
				block_glb = re.sub(pattern=pattern_flags, string=block_glb, repl=combined_flags)
				
			if len(self.changed_flags_glb_new) != 0:
				for line in self.changed_flags_glb_new:
					line_spl = line.split("=")[0]
					changed_pattern = re.compile('(?m)(.*' + re.escape(line_spl) + '.*)')

					changed_line = re.findall(pattern=changed_pattern, string=block_glb)
					block_glb = re.sub(pattern=changed_pattern, string=block_glb, repl=line)


		with open(self.path + "/" + self.partname[-1] + ".glb", "w") as glb_out:
			glb_out.write(block_glb)

		logging.info('Compiler.glb is updated')


#add/removing flags from custom glb
	def add_remove_flag_custom(self):

		if len(self.added_user_falgs) + len(self.removed_user_falgs) != 0:
			(output_rm_custom, error_rm_custom)  = Popen(["rm", "-rf", self.root + "/template_update/" + self.partname[-1] + "_custom.glb"], stdout=PIPE, stderr=PIPE).communicate()
			(output_cp_custom, error_cp_custom)  = Popen(["cp", self.path + "/" + self.partname[-1] + "_custom.glb", self.root + "/template_update"], stdout=PIPE, stderr=PIPE).communicate()
	
		with open(self.path + "/" + self.partname[-1] + "_custom.glb", "r") as custom_in:
			block_custom = custom_in.read()

			if len(self.added_user_falgs) != 0:
			
				with open(self.new_template_path + "/template.glb", "r") as f:
					new_glb = f.read()
				
				added_user= []

				for line in self.added_user_falgs:
					rm_pattern_glb = re.compile('(?ms)((%s).*?)(?=^\S)'%line)
					rm_line = re.findall(pattern=rm_pattern_glb, string=block_custom)
					block_custom = re.sub(pattern=rm_pattern_glb, string=block_custom, repl="")
					
					glb_find_line = re.findall(pattern=rm_pattern_glb, string=new_glb)
					glb_flag = glb_find_line[0][0]
					added_user.append(glb_flag)
				
				pattern_custom_add = re.compile('(?s)(FRONT END.*?)(?=[a-z])')
				custom_line_add = re.findall(pattern=pattern_custom_add, string=block_custom)
				
				custom_flags_block = ",".join(["".join(tup) for tup in custom_line_add])
				custom_combined_flags = "\n".join([custom_flags_block] + added_user)
				
				block_custom = re.sub(pattern=pattern_custom_add, string=block_custom, repl=custom_combined_flags+"\n")
					
			if len(self.removed_user_falgs) != 0:
				for flag in self.removed_user_falgs:
					pattern_custom_rm = re.compile('(?ms)((%s).*?)(?=^\S)'%flag)
					custom_line_rm = re.findall(pattern=pattern_custom_rm, string=block_custom)
					block_custom = re.sub(pattern=pattern_custom_rm, string=block_custom, repl="")
				


		with open(self.path + "/" + self.partname[-1] + "_custom.glb", "w") as custom_out:
			custom_out.write(block_custom)
		
		logging.info('Compiler_custom.glb is updated')
		logging.info('Template update finished sucsessfully')
		
		
update = Tmpupdate(sys.argv[1])

logfile_func = update.logfile()
exist_check_func = update.exist_check()
depot_check_func = update.depot_check()
searcher_func = update.searcher()
permission_func = update.permission()
settingtcl_parse_func = update.settingtcl_parse()
taginfo_func = update.taginfo()
setting_update_func = update.setting_update()
tpllib_update_check_func = update.tpllib_update_check()
