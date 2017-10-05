import asyncio

def async_run(tasks, sem_num=100):
    async def task_runner(task, sem=None):
        if sem:
            async with sem:
                await task
        else:
            await task

    loop = asyncio.new_event_loop()
    sem = asyncio.Semaphore(sem_num, loop=loop)
    try:
        loop.run_until_complete(asyncio.wait([task_runner(task, sem) for task in tasks]))
    except Exception as e:
        print(e)
    finally:
        loop.close()

if __name__ == '__main__':
    import time
    import random
    async def job_runner(num):
        print('job {} start'.format(num))
        start_time = time.time()
        await asyncio.sleep(random.randint(0, 5))
        print('job {} end in {} second'.format(num, time.time() - start_time))

    tasks = [job_runner(num) for num in range(10)]
    async_run(tasks, 5)
