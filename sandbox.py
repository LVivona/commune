import commune as c

# bt = c.module('bittensor')
# print(bt.get_metagraph())


# server = c.import_object('commune.bittensor.neuron.text.server')
# server.serve()
# print(server)

c.new_event_loop()
sample = c.module('dataset').sample()
model = c.connect('server')
print(model.encode_forward_causallmnext(sample['input_ids']))
print(sample)