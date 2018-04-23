SUBDIRS = client server

compile:
	for dir in $(SUBDIRS); do make -C $$dir $@; done

test:
	for dir in $(SUBDIRS); do make -C $$dir $@; done

start:
	for dir in $(SUBDIRS); do make -C $$dir $@; done

.PHONY: compile start
