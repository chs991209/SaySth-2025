def timeit_agent(fn):
    def wrapper(self, *args, **kwargs):
        start = time.time()
        out = fn(self, *args, **kwargs)
        elapsed = time.time() - start
        print(f"[AgentTiming - {self.name}] {elapsed:.2f}s")
        return out
    return wrapper

# Then decorate the relevant methods
# AssistantAgent.generate_reply = timeit_agent(AssistantAgent.generate_reply)