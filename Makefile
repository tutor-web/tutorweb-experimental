SUBDIRS = client server

compile:
	for dir in $(SUBDIRS); do make -C $$dir $@; done

test:
	for dir in $(SUBDIRS); do make -C $$dir $@; done

start:
	for dir in $(SUBDIRS); do make -C $$dir $@; done

lint:
	for dir in $(SUBDIRS); do make -C $$dir $@; done

fakesmtp:
	python3 -m smtpd -n -c DebuggingServer localhost:25

.PHONY: compile start
