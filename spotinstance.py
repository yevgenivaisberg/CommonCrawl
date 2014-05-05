#!/usr/bin/env python
__author__ = 'aub3'

import boto.ec2,time,datetime
CONN = boto.ec2.connect_to_region("us-east-1")

class SpotInstance(object):

    @classmethod
    def get_spot_instances(cls):
        from config import EC2_Tag
        requests = CONN.get_all_spot_instance_requests()
        return [SpotInstance(EC2_Tag,request.id,request.instance_id) for request in requests]


    def __init__(self,tag,request_id=None,instance_id=None,):
        self.request_id = request_id
        self.instance_id = instance_id
        self.public_dns_name = None
        self.price = None
        self.instance_type = None
        self.image_id = None
        self.key_name = None
        self.fulfilled = False
        self.instance_object = None
        self.valid_until = None
        self.tag = tag
        if self.instance_id:
            self.fulfilled = True
            self.get_instance()

    def add_tag(self):
        if self.instance_id:
            CONN.create_tags([self.instance_id], {"Tag":self.tag})


    def request_instance(self,price,instance_type,image_id,key_name):
        self.price = price
        self.instance_type = instance_type
        self.image_id = image_id
        self.key_name = key_name
        print "You are launching a spot instance request."
        print "It is important that you closely monitor and cancel unfilled requests using AWS web console."
        if raw_input("\n Please enter 'yes' to start >> ")=='yes':
            self.valid_until = datetime.datetime.now()+datetime.timedelta(minutes=20) # valid for 20 minutes from now
            spot_request = CONN.request_spot_instances(price=price,instance_type=instance_type,image_id=image_id,key_name=key_name,valid_until=self.valid_until)
            print "requesting a spot instance"
            time.sleep(30) # wait for some time, otherwise AWS throws up an error
            self.request_id = spot_request[0].id
        else:
            print "Did not request a spot instance"

    def check_allocation(self):
        if self.request_id:
            instance_id = CONN.get_all_spot_instance_requests(request_ids=[self.request_id])[0].instance_id
            while instance_id is None:
                print "waiting"
                time.sleep(60) # Checking every minute
                print "Checking job instance id for this spot request"
                instance_id = CONN.get_all_spot_instance_requests(request_ids=[self.request_id])[0].instance_id
                self.instance_id = instance_id
            self.get_instance()

    def get_instance(self):
            reservations = CONN.get_all_reservations()
            for reservation in reservations:
                instances = reservation.instances
                for instance in instances:
                    if instance.id == self.instance_id:
                        self.public_dns_name =  instance.public_dns_name
                        print self.status()
                        self.instance_object = instance
                        return
    def status(self):
        return "request",self.request_id,"spot instance",self.instance_id,"with DNS",self.public_dns_name

    def terminate(self):
        print "terminating spot instance",self.instance_id,self.public_dns_name
        CONN.terminate_instances(instance_ids=[self.instance_id])
