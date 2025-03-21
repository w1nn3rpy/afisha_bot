build:
	docker build -t afisha_bot_image .
run:
	docker run -it -d -v /root/git/afisha_bot:/app/logs -v /root/.config/google-chrome:/root/.config/google-chrome --env-file .env --restart=unless-stopped --name afisha_bot afisha_bot_image
stop:
	docker stop afisha_bot
attach:
	docker attach afisha_bot
dell:
	docker rm afisha_bot
	docker image remove afisha_bot_image
update:
	make stop
	make dell
	make build
	make run