def get_full_user_name(user):
	username = ''
	last_name = ''
	if user.username is not None:
		username = "(@{})".format(user.username)
	if user.last_name is not None:
		last_name = user.last_name
	result = '{} {} {}'.format(user.first_name, username, last_name)
	return result