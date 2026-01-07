FROM rabbitmq:4.1.6-management-alpine
COPY ./plugins/*.ez /opt/rabbitmq/plugins/
RUN rabbitmq-plugins enable rabbitmq_delayed_message_exchange
