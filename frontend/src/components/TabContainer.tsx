import { tabs, PREDICT } from '../lib/constants'
import { Tabs, TabsList, TabsTrigger } from "./ui/tabs";
import React from 'react'
import PageContents from './PageContents';

interface TabsContainerProps {
    defaultValue?: string;
}

export const TabContainer: React.FC<TabsContainerProps> = ({ defaultValue = PREDICT }) => {
    return (
        <Tabs defaultValue={defaultValue} className="w-full">
            <div className='sticky top-0 bg-white z-20 border-b w-screen'>
                <TabsList className='flex gap-4 px-4'>
                    {tabs.map((tab) => (
                        <TabsTrigger
                            key={tab.id}
                            value={tab.id}
                            className="py-2 px-3 text-sm font-medium rounded-md hover:bg-gray-100"
                        >
                            {tab.label}
                        </TabsTrigger>
                    ))
                    }
                </TabsList>
            </div>
            <PageContents />
        </Tabs>
    );
}